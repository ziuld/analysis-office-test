import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from arktic_office.preparation.evidence import Evidence

class ResearchTargetTests(unittest.TestCase):
    def test_complete_path_catalog_is_paginated_and_unsupported_sources_readable(self):
        paths = [f"src/{i:03}.vue" for i in range(250)]
        evidence = Evidence([{"path": p, "text": "const submit = () => axios.post('/contact')"} for p in paths], {"nodes": [], "edges": []})
        seen, offset = [], 0
        while offset is not None:
            page = evidence.lookup({"list_paths": True, "offset": offset})
            seen += page["paths"]
            offset = page["next_offset"]
        self.assertEqual(seen, paths)
        self.assertTrue(evidence.lookup({"paths": [paths[-1]]})["fragments"])
        self.assertIn("error", evidence.respond({"list_paths": True, "offset": -1}))
        self.assertIn("error", evidence.respond({"paths": ["../outside.vue"]}))

    def test_premature_final_must_be_followed_by_source_reading(self):
        from arktic_office.coordination.research import research
        from arktic_office.reporting.questionnaire import VERSION
        snapshot = {"repository": "test", "commit": "a" * 40, "files": [], "questionnaire_version": VERSION}
        evidence = Evidence([{"path": "src/contact.vue", "text": "axios.post('/contact')"}], {"nodes": [], "edges": []})
        config = {"id": "security", "name": "Seguridad", "focus": "Revisar", "files": [], "limits": {"research_rounds": 3, "files": 200, "bytes": 600000}}
        prompts = []
        replies = iter([{"observaciones": [], "respuestas": []}, {"queries": [{"paths": ["src/contact.vue"]}]}, {"observaciones": [], "respuestas": []}])
        def invoke(prompt, config):
            prompts.append(prompt)
            return {"report": json.dumps(next(replies))}
        with tempfile.TemporaryDirectory() as temp:
            state = {}
            research(snapshot, config, state, evidence, invoke, Path(temp), [])
        self.assertEqual(len(prompts), 3)
        self.assertIn("Cierre prematuro", prompts[1])
        self.assertIn("axios.post", prompts[2])
        self.assertEqual(state["archivos"], ["src/contact.vue"])

    def test_extended_rounds_are_configurable(self):
        from arktic_office.config.models import profile
        with patch.dict("os.environ", {"AUDIT_SECURITY_RESEARCH_ROUNDS": "12"}):
            limits = profile("security")["limits"]
        self.assertEqual(limits["research_rounds"], 12)
        self.assertEqual(limits["calls"], 13)

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
