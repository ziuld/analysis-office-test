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
    def test_v14_keeps_compact_persistence_without_requiring_operation_rows(self):
        from arktic_office.reporting.specialist import compose
        source = {'repository':'https://github.com/acme/demo', 'commit':'a'*40,
                  'files':[{'path':'app.py','text':"db = sqlite3.connect('/data/app.db')\n"}]}
        report, _, warnings = compose(json.dumps({'observaciones':[{'observacion':'El código abre SQLite en /data/app.db.', 'certeza':'observado','evidencia':['F1:L1']}]}), source, 'inventory')
        report['celulas'] = [{'id':'inventory','estado':'completada','contrato_salida':'compact-v1'}]
        html = render_html(report, source)
        self.assertFalse(warnings)
        self.assertIn('id="contexto-aplicacion"', html)
        self.assertIn('SQLite en /data/app.db', html)
        self.assertNotIn('id="azure"', html)
        self.assertNotIn('Sin dato estructurado para este aspecto', html)

    def test_v14_risk_is_static_and_unknown_domain_does_not_hide_its_action(self):
        snapshot, data = structured()
        data['confirmados'][0]['control'] = 'por_clasificar'
        valid, _ = prepare_response(json.dumps(data), snapshot)
        html = render_html(valid, snapshot)
        self.assertEqual(html.count('id="R01"'), 1)
        self.assertNotIn('id="destacado-R01"', html)
        controls = html.split('id="controles-objetivo"',1)[1].split('</details>',1)[0]
        self.assertIn('Sin dominio asignado', controls)
        self.assertIn(valid['confirmados'][0]['accion'], controls)
        self.assertIn('No evaluado', html.split('id="controles"',1)[1])
        self.assertIn('beforeprint', html)
        self.assertIn('@media print', html)

    def test_architecture_prompt_example_includes_a_valid_complete_connection(self):
        from arktic_office.reporting.editorial import contract
        prompt = contract("architecture")
        example, _ = json.JSONDecoder().raw_decode(prompt[prompt.index("{"):])
        example = json.loads(json.dumps(example).replace("F1:L7", "F1:L1"))
        snapshot, data = fixture()
        data["presentacion"] = example
        checked, _ = prepare_response(json.dumps(data), snapshot)
        edge = checked["presentacion"]["flujo_actual"]["conexiones"][0]
        self.assertEqual(set(edge), {"origen", "destino", "estado", "descripcion", "evidencia"})
        self.assertEqual(edge["estado"], "inferida")


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

    def test_specialists_receive_one_compact_contract_and_their_role_brief(self):
        snapshot, _ = fixture()
        for cell in CELLS:
            prompt = make_prompt(snapshot, {**cell, "capabilities": []})
            self.assertEqual(prompt.count('CONTRATO DE SALIDA compact-v1'), 1)
            self.assertIn('RESPONSABILIDAD: ' + cell['name'], prompt)
            self.assertNotIn('Comprobación obligatoria del JSON', prompt)
            self.assertNotIn('ESTÁNDAR EDITORIAL COMPARTIDO', prompt)
            self.assertNotIn('\"confirmados\":', prompt)
        self.assertIn(sections()['Consolidación'], instructions())
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

    def test_summary_shows_findings_while_general_gaps_stay_in_annexes(self):
        from arktic_office.reporting.executive import render_markdown
        snapshot, raw = structured()
        raw["dudas"] = ["Confirmar el servidor de producción con el responsable."]
        data, _ = prepare_response(json.dumps(raw), snapshot)
        html = render_html(data, snapshot)
        intro = html.split('id="introduccion"', 1)[1].split('id="situacion-actual"', 1)[0]
        self.assertIn("Entrada concatenada en consulta SQL", intro)
        self.assertNotIn("Confirmar el servidor de producción", intro)
        self.assertNotIn("Resultado y siguiente paso", intro)
        self.assertLess(html.index('id="anexos"'), html.index('id="resultado-lectura"'))
        self.assertIn("Confirmar el servidor de producción", html)
        md = render_markdown(data, snapshot)
        lead = md.split("## 2.", 1)[0]
        self.assertIn("Entrada concatenada en consulta SQL", lead)
        self.assertNotIn("Confirmar el servidor de producción", lead)
        self.assertLess(md.index("## 4. Anexos"), md.index("### Resultado y siguiente paso"))

    def test_summary_has_no_example_specific_defaults(self):
        snapshot, data = fixture()
        valid, _ = prepare_response(json.dumps(data), snapshot)
        html = render_html(valid, snapshot)
        self.assertNotIn('Portal de personal', html)
        self.assertNotIn('director de negocio', html)
        self.assertNotIn('React', html)
        self.assertNotIn('No he podido determinar', html)

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
