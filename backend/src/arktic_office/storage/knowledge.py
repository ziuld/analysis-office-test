"""Transactional review-scoped contributions. Notes never become verified facts."""
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from arktic_office.storage.jsonio import write_json
from arktic_office.preparation.repository import redact


class Knowledge:
    def __init__(self, root):
        self.root = Path(root) / '.knowledge'
        self.root.mkdir(parents=True, exist_ok=True)
        self.database = self.root / 'office.sqlite'
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS revisions (
                  id TEXT PRIMARY KEY, identity TEXT NOT NULL, metadata TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS tasks (
                  run TEXT NOT NULL REFERENCES revisions(id), agent TEXT NOT NULL,
                  assignment TEXT NOT NULL, state TEXT NOT NULL, result TEXT,
                  PRIMARY KEY(run, agent));
                CREATE TABLE IF NOT EXISTS facts (
                  run TEXT NOT NULL, agent TEXT NOT NULL, question TEXT NOT NULL,
                  kind TEXT NOT NULL, payload TEXT NOT NULL,
                  PRIMARY KEY(run, agent, question),
                  FOREIGN KEY(run,agent) REFERENCES tasks(run,agent));
                CREATE TABLE IF NOT EXISTS events (
                  id INTEGER PRIMARY KEY, run TEXT NOT NULL, agent TEXT NOT NULL,
                  payload TEXT NOT NULL, created TEXT DEFAULT CURRENT_TIMESTAMP);
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.database, timeout=15)
        db.execute('PRAGMA foreign_keys=ON')
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def encode(value):
        return redact(json.dumps(value, ensure_ascii=False, sort_keys=True))

    def begin(self, run, snapshot):
        metadata = {k: snapshot.get(k) for k in ('repository', 'commit', 'local_source', 'preparation', 'model_profiles', 'questionnaire_version')}
        # Preparation identity includes the full inventory/tool/rule fingerprint.
        metadata['inventory'] = snapshot.get('inventory', snapshot.get('files', []))
        encoded = self.encode(metadata)
        identity = hashlib.sha256(self.encode({k: v for k,v in metadata.items() if k not in {'model_profiles', 'questionnaire_version'}}).encode()).hexdigest()
        with self.connect() as db:
            existing = db.execute('SELECT identity FROM revisions WHERE id=?', (run,)).fetchone()
            if existing and existing[0] != identity:
                raise ValueError('La identidad de una revisión persistida no puede cambiar.')
            db.execute('INSERT OR IGNORE INTO revisions VALUES (?,?,?)', (run, identity, encoded))
        artifacts = self.root / 'artifacts' / identity
        artifacts.mkdir(parents=True, exist_ok=True)
        if not (artifacts / 'preparation.json').exists():
            write_json(artifacts / 'preparation.json', {k: snapshot.get(k) for k in ('repository','commit','preparation','deterministic_results')})
        return identity

    def task(self, run, config, state, result=None):
        from arktic_office.reporting.questionnaire import catalog
        assignment = {k: config.get(k) for k in ('id', 'focus', 'task', 'limits', 'model', 'reasoning', 'dependencies')}
        assignment['questions'] = catalog(config['id'])
        with self.connect() as db:
            db.execute('INSERT INTO tasks VALUES (?,?,?,?,?) ON CONFLICT(run,agent) DO UPDATE SET state=excluded.state, result=excluded.result',
                       (run, config['id'], self.encode(assignment), self.encode(state), self.encode(result) if result else None))
            db.execute('INSERT INTO events(run,agent,payload) VALUES (?,?,?)', (run, config['id'], self.encode(state)))
            for answer in (result or {}).get('respuestas', []):
                kind = 'observation' if answer['estado'] == 'respondida' else 'hypothesis' if answer['estado'] == 'parcial' else 'pending'
                db.execute('INSERT OR REPLACE INTO facts VALUES (?,?,?,?,?)', (run, config['id'], answer['id'], kind, self.encode(answer)))
            for section, kind in [('confirmados', 'observation'), ('indicios', 'hypothesis'), ('controles', 'control')]:
                for n, item in enumerate((result or {}).get(section, [])):
                    db.execute('INSERT OR REPLACE INTO facts VALUES (?,?,?,?,?)', (run, config['id'], section + ':' + str(n), kind, self.encode(item)))
        return assignment

    def select(self, run, question_ids=None, limit=16):
        with self.connect() as db:
            rows = db.execute('SELECT agent,question,kind,payload FROM facts WHERE run=? ORDER BY question', (run,)).fetchall()
        selected = [{**json.loads(p), 'author': a, 'kind': k} for a, q, k, p in rows if question_ids is None or q in question_ids]
        return selected[:limit]

    def index(self, run):
        """Discovery metadata only: no answers, quotes or model-generated summaries."""
        from arktic_office.reporting.questionnaire import catalog
        with self.connect() as db:
            rows = db.execute('SELECT agent,question,payload FROM facts WHERE run=? ORDER BY question,agent', (run,)).fetchall()
        questions = {q['id']:q for q in catalog()}
        return [{'id':q, 'author':a, 'pregunta':questions[q]['pregunta'],
                 'estado':json.loads(p).get('estado')} for a,q,p in rows if q in questions]

    def answer(self, run, question):
        from arktic_office.core.errors import AuditError
        with self.connect() as db:
            row = db.execute('SELECT agent,payload FROM facts WHERE run=? AND question=? ORDER BY agent', (run,question)).fetchone()
        if row is None:
            raise AuditError('No hay respuesta publicada para '+question+' en esta revisión; no se llama a otro agente.')
        return {**json.loads(row[1]), 'author':row[0]}

    def interrupt(self, run):
        with self.connect() as db:
            rows = db.execute('SELECT agent,state FROM tasks WHERE run=?', (run,)).fetchall()
            for agent, raw in rows:
                state = json.loads(raw)
                if state.get('estado') in {'analizando', 'pendiente', 'preparando'}:
                    state.update(estado='error', execution='interrupted', error='Servicio reiniciado; resultado remoto desconocido. Sin reintento automático.')
                    db.execute('UPDATE tasks SET state=? WHERE run=? AND agent=?', (self.encode(state), run, agent))
                    db.execute('INSERT INTO events(run,agent,payload) VALUES (?,?,?)', (run, agent, self.encode(state)))

    def export(self, directory, config, state, result=None):
        assignment = self.task(directory.name, config, state, result)
        folder = directory / 'agents' / config['id']
        folder.mkdir(parents=True, exist_ok=True)
        write_json(folder / 'assignment.json', assignment)
        if not (folder / 'notes.md').exists():
            (folder / 'notes.md').write_text('Notas de investigación. No constituyen hechos confirmados.\n', encoding='utf-8')
        if result is not None:
            write_json(folder / 'result.json', result)
            summary = '\n'.join(a['id'] + ': ' + a['respuesta'] for a in result.get('respuestas', []))
            (folder / 'summary.md').write_text(redact(summary), encoding='utf-8')
