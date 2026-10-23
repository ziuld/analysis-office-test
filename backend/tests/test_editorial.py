import copy
import hashlib
import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from arktic_office.reporting.editorial import instructions, sections, metadata
from arktic_office.reporting.reports import make_prompt, markdown
from arktic_office.coordination.team import CELLS, prepare_response, consolidate
from arktic_office.reporting.executive import render_html
from arktic_office.preparation.repository import AuditError
from test_security import fixture

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.targets = [], []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'a' and attrs.get('href', '').startswith('#'):
            self.targets.append(attrs['href'][1:])

def structured():
    snapshot, data = fixture()
    data['confirmados'][0].update(titulo='Acceso a datos fuera de lo permitido', resultado_esperado='Las búsquedas no modifican las instrucciones de consulta.', detalle_tecnico='Consulta SQL parametrizada; comprobar permisos efectivos.')
    data['presentacion'] = {'flujo_actual': {'componentes': [
        {'id': 'api', 'nombre': 'Servicio de aplicación', 'descripcion': 'Procesa solicitudes', 'evidencia': ['F1:L1']},
        {'id': 'datos', 'nombre': 'Datos', 'descripcion': 'Información consultada', 'evidencia': ['F1:L1']}],
        'conexiones': [{'origen': 'api', 'destino': 'datos', 'estado': 'inferida', 'descripcion': 'Falta configuración efectiva', 'evidencia': ['F1:L1']}]},
        'estado_operativo': [{'aspecto': 'recuperacion', 'estado': 'no_evaluado', 'descripcion': 'Sin prueba de restauración aportada', 'pendiente': 'Ensayar restauración', 'evidencia': []}]}
    return snapshot, data

class EditorialTests(unittest.TestCase):
    def test_new_generation_requires_risk_wording_but_old_records_still_validate(self):
        import tempfile
        from arktic_office.coordination.team import run_team
        from test_team import snapshot as team_snapshot, fake_invoke
        snapshot, legacy = fixture()
        prepare_response(json.dumps(legacy), snapshot)
        def invoke(prompt, config):
            envelope = fake_invoke(prompt, config)
            if config['id'] == 'security':
                data = json.loads(envelope['report'])
                data['confirmados'][0].update(severidad='media', control='operacion')
                envelope['report'] = json.dumps(data)
            return envelope
        with tempfile.TemporaryDirectory() as temp:
            result = run_team(team_snapshot(), Path(temp), invoke=invoke, emit=lambda *a, **k: None)
        self.assertEqual(result['celulas'][0]['estado'], 'error')
        self.assertIn('título comprensible', result['celulas'][0]['error'])
        self.assertEqual(result['estado'], 'parcial')

    def test_all_prompts_load_common_and_corresponding_section_from_one_source(self):
        snapshot, _ = fixture()
        names = {'security': 'Seguridad', 'architecture': 'Arquitectura', 'inventory': 'Inventario'}
        source = sections()
        for cell in CELLS:
            prompt = make_prompt(snapshot, cell)
            self.assertIn(source['Común'], prompt)
            self.assertIn(source[names[cell['id']]], prompt)
            self.assertEqual(prompt.count('ESTÁNDAR EDITORIAL COMPARTIDO'), 1)
        self.assertIn(source['Consolidación'], instructions())
        self.assertEqual(len(metadata()['sha256']), 64)

    def test_structured_sources_are_resolved_and_missing_data_stays_unknown(self):
        snapshot, data = structured()
        valid, _ = prepare_response(json.dumps(data), snapshot)
        self.assertEqual(valid['presentacion']['flujo_actual']['componentes'][0]['evidencia'][0]['line'], 1)
        html = render_html(valid, snapshot)
        self.assertIn('connection inferida', html)
        self.assertNotIn('Sin dato estructurado para este aspecto.', html)
        self.assertNotIn('id="continuidad"', html)
        self.assertEqual(valid['presentacion']['estado_operativo'][0]['descripcion'], 'Sin prueba de restauración aportada')
        self.assertNotIn('PostgreSQL', html)

    def test_false_structured_sources_and_unknown_nodes_are_rejected(self):
        for mutate in (
            lambda d: d['presentacion']['flujo_actual']['componentes'][0].update(evidencia=['F99:L7']),
            lambda d: d['presentacion']['flujo_actual']['conexiones'][0].update(destino='inventado'),
            lambda d: d['presentacion']['estado_operativo'][0].update(estado='observado'),
        ):
            snapshot, data = structured()
            mutate(data)
            with self.assertRaises(AuditError):
                prepare_response(json.dumps(data), snapshot)

    def test_unsupported_connections_are_not_invented_for_older_results(self):
        snapshot, data = fixture()
        valid, _ = prepare_response(json.dumps(data), snapshot)
        html = render_html(valid, snapshot)
        self.assertNotIn('id="flujo-fuentes"', html)
        self.assertNotIn('class="connection observada"', html)

    def test_every_internal_link_resolves_and_ids_are_unique(self):
        snapshot, data = structured()
        valid, _ = prepare_response(json.dumps(data), snapshot)
        parser = Links()
        parser.feed(render_html(valid, snapshot))
        self.assertEqual(len(parser.ids), len(set(parser.ids)))
        self.assertTrue(set(parser.targets) <= set(parser.ids), str(set(parser.targets) - set(parser.ids)))
        self.assertIn('R01', parser.ids)
        self.assertIn('tecnico-R01', parser.ids)
        self.assertIn('resumen-R01', parser.ids)

    def test_severity_certainty_and_recommendation_remain_separate(self):
        snapshot, data = structured()
        data['indicios'] = [{**data['confirmados'].pop(), 'por_confirmar': 'Falta verificar el acceso efectivo'}]
        valid, _ = prepare_response(json.dumps(data), snapshot)
        html = render_html(valid, snapshot)
        self.assertIn('Gravedad alta', html)
        self.assertIn('Indicio por confirmar', html)
        self.assertIn('Falta verificar el acceso efectivo', html)
        self.assertIn('Recuento de observados: Crítica: **0** · Alta: **0**', markdown(valid, snapshot, 'test'))

    def test_partial_failure_is_visible_and_original_contradictions_survive(self):
        snapshot, data = structured()
        one, _ = prepare_response(json.dumps(data), snapshot)
        two = copy.deepcopy(one)
        two['indicios'] = [{**two['confirmados'].pop(), 'por_confirmar': 'Existe una interpretación diferente'}]
        cells = [{'id': 'security', 'nombre': 'Seguridad', 'estado': 'completada'}, {'id': 'architecture', 'nombre': 'Arquitectura', 'estado': 'error', 'error': 'Respuesta sin fuentes válidas'}]
        combined = consolidate([('security', one), ('architecture', two)], cells)
        self.assertEqual(len(combined['indicios'][0]['aportaciones']), 2)
        html = render_html(combined, snapshot)
        self.assertIn('Resultado parcial', html)
        self.assertIn('Respuesta sin fuentes válidas', html)
        self.assertIn('discrepan', html)
        self.assertIn('Aportaciones originales', html)

    def test_model_html_and_script_payloads_are_literal(self):
        snapshot, data = structured()
        data['confirmados'][0]['titulo'] = '<img src=x onerror=alert(1)>'
        data['confirmados'][0]['detalle_tecnico'] = '</pre><script>alert(1)</script>'
        valid, _ = prepare_response(json.dumps(data), snapshot)
        html = render_html(valid, snapshot)
        self.assertNotIn('<img src=x', html)
        self.assertNotIn('<script>alert(1)', html)
        self.assertIn('&lt;script&gt;alert(1)', html)

    def test_summary_has_no_example_specific_defaults(self):
        snapshot, data = fixture()
        valid, _ = prepare_response(json.dumps(data), snapshot)
        html = render_html(valid, snapshot)
        self.assertNotIn('Portal de personal', html)
        self.assertNotIn('director de negocio', html)
        self.assertNotIn('React', html)
        self.assertIn('No he podido determinar', html)

    def test_markdown_keeps_populated_sections_and_sources(self):
        snapshot, data = structured()
        valid, _ = prepare_response(json.dumps(data), snapshot)
        md = markdown(valid, snapshot, 'test')
        for title in ('Resumen del informe', 'Flujo actual de la aplicación', 'Diagnóstico y riesgos', 'Controles y mejoras', 'Anexos'):
            self.assertIn(title, md)
        for title in ('Base de datos y recuperación', '### Inventario', 'Arquitectura propuesta en Azure', 'Decisión y siguientes pasos'):
            self.assertNotIn(title, md)
        self.assertIn('resultado', md.lower())
        self.assertIn('routes.py#L1', md)

    def test_reference_v12_is_unchanged_when_present(self):
        roots = [p for p in Path(__file__).resolve().parents if (p / 'pyproject.toml').is_file()]
        if not roots:
            self.skipTest('Referencia visual local ausente del contenedor de regresión')
        reference = roots[0] / 'artifacts/propuesta-informe-direccion-arktic-v12.html'
        if reference.is_file():
            self.assertEqual(hashlib.sha256(reference.read_bytes()).hexdigest(), '2936f4a42ca4a45db2168a42b29c2d3753b1a1d32ca7179dcda1e6a2ae2eea44')
