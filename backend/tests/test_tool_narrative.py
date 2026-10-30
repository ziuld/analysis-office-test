import json
import unittest
from arktic_office.reporting.questionnaire_view import deterministic_html, markdown
from arktic_office.reporting.tool_narrative import narrative


class ToolNarrativeTests(unittest.TestCase):
    def test_all_alerts_are_explained_without_raw_code_or_json(self):
        tools = [
            {'id': 'D02', 'name': 'Gitleaks', 'status': 'detecciones_por_validar', 'detail': 'sin historial',
             'result': {'input_files': ['config.env'], 'findings': [{'path': 'config.env', 'line': 3}], 'original_output_redacted': {'Secret': 'RAW_PRIVATE_MARKER'}}},
            {'id': 'D03', 'name': 'OSV-Scanner', 'status': 'detecciones_por_validar', 'detail': '',
             'result': {'findings': [{'path': 'pnpm-lock.yaml', 'summary': f'package{i} 1.0 · CVE-2026-1234. Coincidencia de versión.'} for i in range(25)]}},
            {'id': 'D04', 'name': 'Semgrep', 'status': 'detecciones_por_validar', 'detail': '',
             'result': {'processed_files': ['<script>evil</script>.js'], 'findings': [{'path': '<script>evil</script>.js', 'summary': 'Patrón SAST · arktic.js-dynamic-execution.'}], 'original_output_redacted': {'code': 'eval(user_input)'}}},
            {'id': 'D05', 'name': 'Graphify', 'status': 'partial', 'detail': '',
             'result': {'nodes': [{'id': 'RAW_NODE_ID'}], 'edges': [], 'file_coverage': [{'path': 'app.vue', 'status': 'unsupported', 'reason': 'no_static_parser'}]}}
        ]
        original = json.dumps(tools)
        data = {'deterministic_results': {'repository': 'example', 'commit': 'a'*40, 'tools': tools,
                'preparation_cache': {'status': 'reused', 'prepared_at': '2026-10-29'}}}
        html = deterministic_html(data)
        md = markdown(data, {})
        self.assertNotIn('<pre', html)
        for raw in ('RAW_PRIVATE_MARKER', 'RAW_NODE_ID', 'eval(user_input)', 'original_output_redacted', '```'):
            self.assertNotIn(raw, html)
            self.assertNotIn(raw, md)
        self.assertIn('package24 1.0', html)
        self.assertIn('CVE-2026-1234', html)
        self.assertIn('Ejecución dinámica', html)
        self.assertIn('&lt;script&gt;evil&lt;/script&gt;.js', html)
        self.assertNotIn('<script>evil</script>', html)
        self.assertIn('sin analizar el historial', html)
        self.assertIn('Preparación reutilizada', html)
        self.assertEqual(json.dumps(tools), original)

    def test_unevaluated_is_not_presented_as_a_clean_check(self):
        state, paragraphs, _ = narrative({'id': 'D03', 'name': 'OSV', 'status': 'no_evaluado', 'result': {}, 'detail': ''})
        self.assertEqual(state, 'No evaluado')
        self.assertIn('no puede interpretarse como un resultado favorable', ' '.join(paragraphs))
