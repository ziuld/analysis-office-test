import unittest
from arktic_office.preparation.evidence import Evidence

class ResearchTargetTests(unittest.TestCase):
    def test_http_auth_and_recovery_read_definitions_not_previous_calls(self):
        for symbol, implementation in [("do_GET", "    require_permission(user)"), ("recover_jobs", "    state = 'error'")]:
            text = symbol + "()\n" + "# padding\n" * 310 + "def " + symbol + "():\n" + implementation
            graph = {"nodes": [{"id": symbol, "label": symbol + "()", "source_file": "server.py", "source_location": "L312"}], "edges": []}
            evidence = Evidence([{"path": "server.py", "text": text}], graph)
            files, trace = evidence.batch([{"paths": ["server.py"], "query": symbol}], {"files": 1, "bytes": 12000})
            self.assertEqual(files[0]["text"].splitlines()[311], "def " + symbol + "():")
            self.assertEqual(files[0]["text"].splitlines()[312], implementation)
            self.assertGreater(trace[0]["result"]["fragments"][0]["start"], 1)
            self.assertFalse(trace[0]["result"]["omitted_by_budget"])

    def test_overgrouped_paths_split_only_inside_existing_lookup_budget(self):
        paths = [f"f{i}.py" for i in range(12)]
        evidence = Evidence([{"path": p, "text": "value = 1"} for p in paths], {"nodes": [], "edges": []})
        limits = {"files": 20, "bytes": 100000}
        files, trace = evidence.batch([{"paths": paths[:5]}, {"paths": paths[5:8]}, {"paths": paths[8:11]}], limits)
        self.assertEqual(len(trace), 4)
        self.assertEqual(len(files), 11)
        self.assertTrue(all(len(q["request"]["paths"]) <= 3 for q in trace))
        self.assertEqual(trace[0]["result"]["request_split"], {"original_paths": 5, "part": 1, "parts": 2})
        self.assertEqual(trace[1]["result"]["request_split"]["part"], 2)
        files, trace = evidence.batch([{"paths": paths[:5]}] + [{"paths": [p]} for p in paths[5:8]], limits)
        self.assertEqual(len(trace), 4)
        self.assertIn("error", trace[0]["result"])
        self.assertEqual(len(files), 3)
        files, trace = evidence.batch([{"paths": ["../escape.py"] * 5}], limits)
        self.assertFalse(files)
        self.assertTrue(all(q["result"].get("error") for q in trace))
