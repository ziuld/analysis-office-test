"""Only retrieval boundaries and bounded exploration; no live clients or tools."""
import base64
import json
import unittest
from unittest.mock import patch
from arktic_office.core.errors import AuditError
from arktic_office.preparation.hybrid import prepare, Retrieval, explore, LIMITS


class HybridTests(unittest.TestCase):
    def test_one_acquisition_scanner_scope_and_verified_flow(self):
        sources = {"api/controller.py": "from service import reserve\ndef route():\n    return reserve()",
                   "api/service.py": "from repository import save\ndef reserve():\n    return save()",
                   "api/repository.py": "def save():\n    return db.insert()\npassword = 'private-value'"}
        calls, scans, events = [], [], []
        def fetch(endpoint):
            calls.append(endpoint)
            if endpoint == "/repos/acme/app":
                return {"default_branch": "develop"}
            if "/branches/" in endpoint:
                return {"commit": {"sha": "b" * 40, "commit": {"tree": {"sha": "tree"}}}}
            if "/git/trees/" in endpoint:
                return {"tree": [{"type": "blob", "mode": "100644", "path": p, "size": len(t.encode()), "sha": p}
                                 for p, t in sources.items()]}
            return {"encoding": "base64", "content": base64.b64encode(sources[endpoint.split("/git/blobs/")[1]].encode()).decode()}
        def scanner(files):
            scans.append(files)
            return []
        actions = iter([{"tool": "read", "path": p, "start": 1, "end": 2} for p in sources]
                       + [{"tool": "finish", "reason": "Tres capas leídas; persistencia externa pendiente."}])
        def invoke(prompt, config):
            self.assertNotIn("private-value", prompt)
            return {"report": json.dumps(next(actions)), "usage": {"total_tokens": 10}}
        with patch.dict("os.environ", {"AUDIT_PREPARATION_MAX_LOOPS": "3"}):
            snapshot = prepare("https://github.com/acme/app", fetch=fetch, scanner=scanner, invoke=invoke,
                               config={}, index=lambda files: {"status": "ready", "nodes": [], "edges": []}, emit=events.append)
        self.assertEqual(snapshot["commit"], "b" * 40)
        self.assertEqual(len(scans), 1)
        self.assertEqual(len([c for c in calls if "/git/blobs/" in c]), 3)
        self.assertEqual(snapshot["preparation"]["exploration"]["closure"], "sufficient")
        self.assertEqual(len(snapshot["coverage"]["explorer_reads"]), 3)
        controller = next(f for f in snapshot["files"] if f["path"] == "api/controller.py")
        self.assertEqual(controller["text"].splitlines()[1], "def route():")
        self.assertEqual(events[-1]["events"][-1]["event"], "closed")
        self.assertEqual(len(snapshot["coverage"]["scanner_input"]), 3)
        from test_security import fixture
        from arktic_office.coordination.team import prepare_response
        from arktic_office.reporting.executive import render_html, render_markdown
        old_snapshot, raw_report = fixture()
        report, _ = prepare_response(json.dumps(raw_report), old_snapshot)
        old_snapshot.update(preparation=snapshot["preparation"], coverage=snapshot["coverage"])
        for rendered in (render_html(report, old_snapshot), render_markdown(report, old_snapshot)):
            self.assertIn("Entrada a scanners", rendered)
            self.assertIn("explorador declaró suficiente", rendered)

    def test_restrictions_limits_and_useful_partial_evidence(self):
        snapshot = {"commit": "a" * 40, "files": [], "bytes_read": 0,
                    "limits": {"files": 2, "file_bytes": 12000, "total_bytes": 24000}}
        retrieval = Retrieval([{"path": "src/a.py", "text": "one\ntwo\nthree"}], snapshot,
                              {"status": "error", "reason": "index_unavailable"})
        for action in ({"tool": "shell"}, {"tool": "read", "path": "../a", "start": 1, "end": 1},
                       {"tool": "read", "path": "src/a.py", "start": 4, "end": 101}):
            with self.assertRaises(AuditError):
                retrieval.tool(action)
        result = retrieval.tool({"tool": "read", "path": "src/a.py", "start": 2, "end": 2})
        self.assertEqual(result["text"], "two")
        self.assertEqual(snapshot["files"][0]["text"], "\ntwo\n")
        self.assertEqual(retrieval.tool({"tool": "search", "query": "two"})["hits"][0]["line"], 2)
        self.assertEqual(retrieval.tool({"tool": "graph", "query": "two"})["status"], "error")
        clipped = retrieval.tool({"tool": "read", "path": "src/a.py", "start": 1, "end": 101})
        self.assertEqual((clipped["start"], clipped["end"], clipped["requested_end"]), (1, 3, 101))
        self.assertTrue(clipped["limited"])
        state = explore(retrieval, lambda *a: {"report": '{"tool":"search","query":"two"}'}, {})
        self.assertEqual(state["closure"], "iteration_limit")
        self.assertEqual(state["iterations"], state["limits"]["iterations"])
        state = explore(retrieval, lambda *a: {"report": '{"tool":"shell"}'}, {})
        self.assertEqual(state["closure"], "technical_error")
        self.assertIn("two", snapshot["files"][0]["text"])
        from unittest.mock import patch
        with patch.dict(LIMITS, {"prompt_bytes": 1}):
            state = explore(retrieval, lambda *a: self.fail("No budget: must not invoke"), {})
        self.assertEqual(state["closure"], "context_limit")
        with patch.dict(LIMITS, {"seconds": 0}):
            state = explore(retrieval, lambda *a: self.fail("No time: must not invoke"), {})
        self.assertEqual(state["closure"], "time_limit")
        retrieval.pool["src/a.py"] = "\n".join(str(n) for n in range(220))
        clipped = retrieval.tool({"tool": "read", "path": "src/a.py", "start": 95, "end": 197})
        self.assertEqual(clipped["end"], 194)
        self.assertEqual(len(clipped["text"].splitlines()), 100)

    def test_extra_loops_add_to_initial_pass_and_finish_can_stop_early(self):
        for loops in (0, 1, 2, 3):
            with self.subTest(loops=loops), patch.dict("os.environ", {"AUDIT_PREPARATION_MAX_LOOPS": str(loops)}):
                snapshot = {"commit": "a" * 40, "files": [], "bytes_read": 0,
                            "limits": {"files": 2, "file_bytes": 12000, "total_bytes": 24000}}
                retrieval = Retrieval([{"path": "a.py", "text": "one"}], snapshot, {})
                calls = []
                def invoke(prompt, config):
                    calls.append(prompt)
                    self.assertIn(f"máximo {1 + loops} turnos", prompt)
                    return {"report": '{"tool":"read","path":"a.py","start":1,"end":1}'}
                state = explore(retrieval, invoke, {})
                self.assertEqual(len(calls), 1 + loops)
                self.assertEqual(state["limits"]["max_loops"], loops)
                self.assertEqual(state["closure"], "iteration_limit")
                self.assertEqual(snapshot["files"][0]["text"], "one")
                finish = unittest.mock.Mock(return_value={"report": '{"tool":"finish","reason":"Código leído; suficiente."}'})
                state = explore(retrieval, finish, {})
                self.assertEqual(finish.call_count, 1)
                self.assertEqual(state["closure"], "sufficient")
