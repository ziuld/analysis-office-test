"""Central execution, persistence and failure boundaries; zero real provider calls."""
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from arktic_office.adapters.invoke import ProviderError
from arktic_office.coordination.catalog import catalog as profiles
from arktic_office.coordination.team import CELLS, run_team
from arktic_office.execution.budget import Budget
from arktic_office.execution.jobs import Jobs
from arktic_office.preparation.evidence import Evidence
from arktic_office.reporting.questionnaire import catalog
from arktic_office.resources.paths import resource_path
from arktic_office.storage.knowledge import Knowledge
from arktic_office.storage.jsonio import read_json, write_json
from test_team import snapshot, fake_invoke
from test_questions import fixture


class CentralTests(unittest.TestCase):
    def test_questions_match_frozen_reference_and_have_exact_ownership(self):
        reference = json.loads(resource_path('profiles', 'questions-reference.json').read_text(encoding='utf-8'))
        self.assertEqual([(q['id'], q['pregunta']) for q in catalog()], [(q['id'], q['pregunta']) for q in reference])
        self.assertEqual(len(catalog()), 40)
        expected = {'coordinator': [1,2,3,38,39,40], 'inventory': list(range(4,7)), 'architecture': list(range(7,10)),
                    'data': list(range(10,15)), 'devops': list(range(15,23)), 'identity': list(range(23,28)),
                    'frontend-security': list(range(28,32)), 'backend-security': list(range(32,38))}
        for role, numbers in expected.items():
            self.assertEqual([q['id'] for q in catalog(role)], [f'Q{n:02}' for n in numbers])
        self.assertEqual(len(profiles()), 8)
        self.assertEqual([c['id'] for c in CELLS], ['inventory','architecture','data','identity','frontend-security','backend-security','devops'])

    def test_lightweight_listing_keeps_flags_from_older_manifests(self):
        from arktic_office.storage.runs import RunStore
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)/'saved-review'
            fixture(directory)
            evidence = read_json(directory/'evidencia.json')
            evidence.update(simulation=True, source_revision='source-review', evidence_origin='Saved evidence')
            write_json(directory/'evidencia.json', evidence)
            write_json(directory/'manifest.json', {k:evidence[k] for k in ('repository','commit')})
            store = RunStore(temp)
            complete, brief = store.record(directory), store.record(directory, brief=True)
            for key in ('simulation','derived_from','evidence_origin','report_format'):
                self.assertEqual(complete[key], brief[key])
            self.assertTrue(brief['simulation'])

    def test_content_search_survives_filename_match_and_pages_every_occurrence(self):
        evidence = Evidence([{'path':'target.txt','text':'unrelated'}, {'path':'source.vue','text':'\n'.join(['target'] * 8)}], {})
        seen, offset = [], 0
        while offset is not None:
            result = evidence.lookup({'query':'target', 'offset': offset})
            seen.extend((m['path'],m['line']) for m in result['matches'])
            offset = result['next_offset']
        self.assertTrue(all(('source.vue', n) in seen for n in range(1,9)))
        self.assertEqual(len(seen), len(set(seen)))
        self.assertEqual(evidence.lookup({'list_paths':True, 'offset':0, 'query':'list_paths'})['paths'],
                         evidence.lookup({'list_paths':True, 'offset':0})['paths'])
        self.assertIn('error', evidence.respond({'list_paths':True, 'query':'unrelated'}))

    def test_knowledge_is_scoped_persistent_and_not_overwritten_by_other_commit(self):
        with tempfile.TemporaryDirectory() as temp:
            store = Knowledge(temp)
            store.begin('review-a', snapshot())
            config = {**CELLS[0], 'limits': {}, 'model': 'configured'}
            answer = {**catalog('inventory')[0], 'estado':'respondida', 'respuesta':'Node declarado',
                      'evidencia':[{'path':'Dockerfile','line':1,'quote':'FROM node:22'}]}
            store.task('review-a', config, {'estado':'completada'}, {'respuestas':[answer]})
            reopened = Knowledge(temp)
            self.assertEqual(reopened.select('review-a')[0]['author'], 'inventory')
            self.assertEqual(reopened.select('review-b'), [])
            with self.assertRaises(ValueError):
                reopened.begin('review-a', {**snapshot(), 'commit':'b'*40})

    def test_provider_failure_stops_new_calls_and_preserves_valid_results(self):
        calls = []
        def invoke(prompt, config):
            calls.append(config['id'])
            if config['id'] == 'architecture':
                raise ProviderError('Sesión no válida')
            return fake_invoke(prompt, config)
        with tempfile.TemporaryDirectory() as temp:
            data = run_team(snapshot(), Path(temp), invoke=invoke, emit=lambda *a, **k: None)
            self.assertEqual(calls, ['inventory','architecture'])
            self.assertTrue(data['confirmados'])
            self.assertTrue(all(c['estado'] == 'bloqueado' for c in data['celulas'][2:]))
            self.assertTrue(data['stop_reason'])
            self.assertTrue((Path(temp)/'agents/inventory/result.json').is_file())

    def test_budget_reserves_once_and_reports_missing_provider_metrics(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {'AUDIT_REVIEW_MAX_CALLS':'1'}):
            calls = []
            budget = Budget(lambda p,c: calls.append(c) or {'report':'{}'}, Path(temp))
            config = {'model':'configured', 'max_output_tokens':1000}
            budget('first', config)
            from arktic_office.core.errors import AuditError
            with self.assertRaises(AuditError):
                budget('second', config)
            self.assertEqual(len(calls), 1)
            metrics = read_json(Path(temp)/'metrics.json')
            self.assertIsNone(metrics['calls'][0]['usage'])
            self.assertEqual(metrics['calls'][0]['prompt_bytes'], 5)

    def test_missing_required_result_blocks_only_its_dependents(self):
        agents = [{**c, 'dependencies':['inventory'] if c['id']=='architecture' else []} for c in CELLS]
        calls = []
        from arktic_office.core.errors import AuditError
        def invoke(prompt, config):
            calls.append(config['id'])
            if config['id']=='inventory':
                raise AuditError('Fallo local de una especialidad')
            return fake_invoke(prompt, config)
        with tempfile.TemporaryDirectory() as temp, patch('arktic_office.coordination.team.CELLS', agents):
            data = run_team(snapshot(), Path(temp), invoke=invoke, emit=lambda *a, **k: None)
        self.assertNotIn('architecture', calls)
        self.assertIn('data', calls)
        self.assertEqual(data['celulas'][1]['estado'], 'bloqueado')
        self.assertTrue(data['confirmados'])

    def test_provider_excess_over_a_soft_cap_stops_the_next_call(self):
        from arktic_office.core.errors import AuditError
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {'AUDIT_REVIEW_MAX_CALLS':'3', 'AUDIT_REVIEW_OUTPUT_TOKENS':'2000'}):
            budget = Budget(lambda *a: {'report':'{}', 'usage':{'output_tokens':2500}}, Path(temp))
            config = {'model':'configured', 'max_output_tokens':1000}
            budget('first', config)
            self.assertEqual(budget.charged_output_tokens(), 2500)
            with self.assertRaises(AuditError):
                budget('second', config)
            self.assertEqual(len(budget.calls), 1)

    def test_each_new_profile_has_a_saved_context_and_functional_query(self):
        from arktic_office.coordination.questions import prepare_question, answer_question
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)/'saved-review'
            fixture(directory)
            source = read_json(directory/'celulas/security.json')
            for agent in CELLS:
                write_json(directory/'celulas'/ (agent['id']+'.json'), {**source, 'id':agent['id']})
                context = prepare_question(directory, agent['id'], 'Explica la evidencia')
                self.assertEqual(context['agent'], agent['id'])
                answer = answer_question(context, invoke=lambda *a: {'report':json.dumps({'respuesta':'No hay mediciones.', 'certeza':'sin_informacion','evidencia':[]})})
                self.assertEqual(answer['certeza'], 'sin_informacion')

    def test_sqlite_interruption_preserves_finished_results(self):
        with tempfile.TemporaryDirectory() as temp:
            store = Knowledge(temp)
            store.begin('review-a', snapshot())
            store.task('review-a', CELLS[0], {'estado':'completada'}, {'respuestas':[],'value':'conservar'})
            store.task('review-a', CELLS[1], {'estado':'analizando'})
            store.interrupt('review-a')
            with store.connect() as db:
                completed = db.execute('SELECT result FROM tasks WHERE run=? AND agent=?', ('review-a','inventory')).fetchone()[0]
                interrupted = db.execute('SELECT state FROM tasks WHERE run=? AND agent=?', ('review-a','architecture')).fetchone()[0]
            self.assertEqual(json.loads(completed)['value'], 'conservar')
            self.assertEqual(json.loads(interrupted)['execution'], 'interrupted')

    def test_published_question_id_never_publishes_model_activity_or_calls_it(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            directory = root/'saved-review'
            fixture(directory)
            report = read_json(directory/'informe.json')
            report['cuestionario'] = {'respuestas':[{'id':'Q08','estado':'respondida','respuesta':'Conexión guardada.', 'evidencia':[]}]}
            write_json(directory/'informe.json', report)
            events = []
            jobs = Jobs(root, answerer=lambda *a:self.fail('Cached fact must not call a model'), event_sink=events.append)
            query = jobs.ask(directory.name, 'coordinator', 'Q08')
            deadline = time.monotonic()+3
            while jobs.question(directory.name, query['id'])['estado'] != 'completada' and time.monotonic()<deadline:
                time.sleep(.01)
            result = jobs.question(directory.name, query['id'])
            self.assertEqual(result['source'], 'core')
            self.assertIsNone(result['model'])
            self.assertFalse(any(e.state=='respondiendo' for e in events))

    def test_queries_wait_for_review_and_then_execute_sequentially(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            directory = root/'saved-review'
            fixture(directory)
            started, release = threading.Event(), threading.Event()
            invocations = []
            def runner(run_id, repository):
                started.set()
                release.wait(3)
                write_json(jobs.directory(run_id)/'informe.json', {'estado':'completo'})
                return 0
            def answerer(context):
                invocations.append(context['agent'])
                return {'respuesta':'Hecho guardado', 'certeza':'explicacion', 'evidencia':[]}
            jobs = Jobs(root, runner=runner, answerer=answerer)
            job = jobs.start('https://github.com/acme/test')
            self.assertTrue(started.wait(2))
            first = jobs.ask(directory.name, 'coordinator', 'Pregunta uno')
            second = jobs.ask(directory.name, 'coordinator', 'Pregunta dos')
            self.assertEqual(first['estado'], 'en_cola')
            self.assertFalse(invocations)
            release.set()
            deadline = time.monotonic()+4
            while jobs.question(directory.name, second['id'])['estado'] not in {'error','completada'} and time.monotonic() < deadline:
                time.sleep(.01)
            self.assertEqual(invocations, ['coordinator','coordinator'])
            self.assertEqual(jobs.question(directory.name, first['id'])['estado'], 'completada')
