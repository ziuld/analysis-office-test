import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from arktic_office.config.agents import read_profiles
from arktic_office.coordination.initial_sources import select
from arktic_office.coordination.research import research
from arktic_office.coordination.team import cell_config, run_team
from arktic_office.preparation.evidence import Evidence
from test_questionnaire import fixture


class InitialSourcesTests(unittest.TestCase):
    def test_first_call_receives_citable_sources_and_can_finish(self):
        snapshot, _ = fixture()
        evidence = Evidence([{'path': path, 'text': text} for path, text in (
            ('README.md', '# Project\n## Arranque local\nUsa pnpm dev.\n'),
            ('turbo.json', '{"tasks":{"build":{"dependsOn":["^build"]}}}'),
            ('package.json', '{"scripts":{"dev":"turbo dev"}}'),
            ('apps/web/package.json', '{"scripts":{"dev":"next dev"}}'),
            ('.env', 'TOKEN=do-not-send-test-value'),
        )], {})
        profile = next(p for p in read_profiles() if p['id'] == 'devops')
        config = {**profile, **cell_config(profile)}
        calls = []

        def invoke(prompt, _):
            calls.append(prompt)
            return {'report': json.dumps({'observaciones': []})}

        with tempfile.TemporaryDirectory() as folder:
            state = {}
            research(snapshot, config, state, evidence, invoke, Path(folder), [state])
        self.assertEqual(len(calls), 1)
        self.assertIn('"path":"turbo.json"', calls[0])
        self.assertIn('L2 | ## Arranque local', calls[0])
        self.assertNotIn('do-not-send-test-value', calls[0])
        self.assertIn('turbo.json', state['archivos'])
        self.assertEqual(state['initial_sources']['pending_count'], 0)

        limits = {'files': 1, 'bytes': 60}
        files, trace = select('devops', evidence, limits)
        self.assertEqual([f['path'] for f in files], ['package.json'])
        self.assertLessEqual(trace['bytes'], 60)
        self.assertIn('turbo.json', trace['pending_paths'])

    def test_independent_profiles_select_distinct_bounded_sources(self):
        expected = {
            'inventory': 'pom.xml',
            'architecture': 'api/MainApplication.java',
            'data': 'packages/database/schema.prisma',
            'identity': 'server/auth.py',
            'frontend-security': 'apps/web/src/lib/sanitize-html.ts',
            'backend-security': 'apps/backend/app/v1/public/leads/route.ts',
            'devops': 'turbo.json',
        }
        evidence = Evidence([{'path': path, 'text': 'A source with evidence.'} for path in expected.values()], {})
        limits = {'files': 200, 'bytes': 600000}
        for profile in read_profiles():
            role = profile['id']
            with self.subTest(role=role):
                self.assertTrue(profile['questions'])
                files, trace = select(role, evidence, limits)
                paths = [f['path'] for f in files]
                self.assertIn(expected[role], paths)
                self.assertEqual(len(paths), len(set(paths)))
                if role != 'devops':
                    self.assertLessEqual(len(paths), 5)
                    self.assertLessEqual(trace['bytes'], 4400)

    def test_full_stack_answers_all_questions_without_invoking_the_team(self):
        from arktic_office.config.agents import FULL_STACK
        from arktic_office.coordination.iris import load_tasks
        from arktic_office.reporting.questionnaire import catalog
        from arktic_office.reporting.view import render_html, render_markdown

        snapshot, _ = fixture()
        snapshot['request']['full_stack'] = True
        evidence = Evidence([{'path': 'package.json', 'text': '{}'}], {})
        calls = []
        tasks = {task['id']: task for task in load_tasks()}

        def invoke(prompt, config):
            calls.append(config['id'])
            task = tasks[config['task_id']]
            if task['id'] == 'aplicacion':
                self.assertIn('"path":"package.json"', prompt)
            return {'report': json.dumps({'comprobar': ['Contrastar la configuración.'],
                'cierre': 'Queda por comprobar el resto de la configuración.', 'respuestas': [
                    {'id': key, 'estado': 'parcial', 'respuesta': 'Resultado de Iris ' + key}
                    for key in task['questions']]})}

        with tempfile.TemporaryDirectory() as folder:
            report = run_team(snapshot, Path(folder), invoke=invoke, evidence=evidence)
        self.assertEqual(calls, [FULL_STACK] * len(tasks))
        answers = report['cuestionario']['respuestas']
        self.assertEqual([q['id'] for q in answers], [q['id'] for q in catalog()])
        self.assertTrue(all(q['role'] == FULL_STACK and q['respuesta'].endswith(q['id']) for q in answers))
        self.assertIn('Iris · Full Stack', render_html(report, snapshot))
        self.assertIn('Iris · Full Stack', render_markdown(report, snapshot))

    def test_removed_profile_leaves_its_questions_explicitly_unassigned(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'agents.json').write_text('[{"id":"devops"}]', encoding='utf-8')
            with patch('arktic_office.config.agents.resource_path', return_value=root):
                self.assertEqual(read_profiles(), ())
            snapshot, _ = fixture()
            snapshot['request']['mode'] = 'deterministic'
            with patch('arktic_office.coordination.team.CELLS', ()):
                report = run_team(snapshot, root, invoke=lambda *_: self.fail('Llamada inesperada'))
        answers = {q['id']: q for q in report['cuestionario']['respuestas']}
        self.assertEqual(len(answers), 40)
        self.assertEqual(answers['Q15']['estado'], 'no_comprobado')
        self.assertEqual(answers['Q15']['respuesta'], 'Pregunta sin responsable activo.')
