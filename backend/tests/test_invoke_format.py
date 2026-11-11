import unittest
import json
from types import SimpleNamespace
from unittest.mock import patch
from arktic_office.adapters.invoke import invoke_hermes, normalize_json_report
from arktic_office.config.agents import FULL_STACK


class InvokeFormatTests(unittest.TestCase):
    def test_known_suffix_preserves_complete_object(self):
        self.assertEqual(normalize_json_report('{"observaciones":[]} </final>\n'), '{"observaciones":[]}')

    def test_does_not_repair_or_extract_arbitrary_content(self):
        for raw in ('{"observaciones":[]', '{"a":1} comentario</final>',
                    'prefacio {"a":1}</final>', '[1]</final>', '{"a":1}{"b":2}</final>'):
            with self.subTest(raw=raw):
                self.assertEqual(normalize_json_report(raw), raw)

    def test_legitimate_json_and_tag_inside_string_remain_unchanged(self):
        for raw in ('{"a":1}\n', '{"a":"</final>"}'):
            self.assertEqual(normalize_json_report(raw), raw)

    def test_adapter_normalizes_before_dispatch_and_retains_usage(self):
        process = SimpleNamespace(returncode=0, stdout=json.dumps({"report":'{"observaciones":[]}</final>', "usage":{"total_tokens":7}}))
        with patch('arktic_office.adapters.invoke.subprocess.run', return_value=process):
            envelope = invoke_hermes('fixture', {"model":"fixture", "reasoning":"low"})
        self.assertEqual(json.loads(envelope['report']), {"observaciones":[]})
        self.assertEqual(envelope['usage']['total_tokens'], 7)
        self.assertEqual(envelope['format_normalization'], 'removed_final_closing_tag')

    def test_iris_codex_idle_default_preserves_operator_override(self):
        setting = "HERMES_CODEX_EVENT_STALE_TIMEOUT_SECONDS"
        process = SimpleNamespace(returncode=0, stdout='{"report":"{}"}')
        for agent, provider, overrides, expected in (
            (FULL_STACK, "openai-codex", {}, "90"),
            (FULL_STACK, "openai-codex", {setting: "75"}, "75"),
            (FULL_STACK, "openai", {}, None),
            ("identity", "openai-codex", {}, None),
        ):
            with self.subTest(agent=agent, provider=provider, expected=expected):
                with patch.dict("os.environ", overrides, clear=True), patch(
                        "arktic_office.adapters.invoke.subprocess.run", return_value=process) as run:
                    invoke_hermes("fixture", {"id": agent, "provider": provider, "model": "fixture",
                                              "reasoning": "medium", "timeout": 240})
                self.assertEqual(run.call_args.kwargs["env"].get(setting), expected)
                self.assertEqual(run.call_args.kwargs["timeout"], 240)
