"""Pinned Graphify API over an explicit complete file list; no ignore rules or LLM."""
import json
import sys
from pathlib import Path
from graphify.extract import extract, _DISPATCH

root, output = Path(sys.argv[1]).resolve(), Path(sys.argv[2])
all_files = sorted(p for p in root.rglob("*") if p.is_file())
supported = [p for p in all_files if p.suffix in _DISPATCH or p.suffix.lower() in _DISPATCH]
result = extract(supported, root=root, max_workers=2)

def relative(value):
    path = Path(value)
    return path.relative_to(root).as_posix() if path.is_absolute() else path.as_posix()

failed = {relative(p) for p in result.get("failed_sources", [])}
skipped = {relative(p) for p in result.get("skipped_sources", [])}
unsupported = {}
for p in supported:
    relative_path = p.relative_to(root).as_posix()
    if relative_path not in failed | skipped:
        continue
    # Native YAML dialect/data exclusions are incompatibility, not successful AST coverage.
    if p.suffix.lower() in {".yaml", ".yml"}:
        detail = _DISPATCH[p.suffix.lower()](p)
        reason = detail.get("skipped")
        error = str(detail.get("error", ""))
        if reason in {"scalar yaml", "data yaml (not a config/manifest)"} or "could not determine a constructor for the tag" in error or "could not determine a constructor for tag" in error:
            unsupported[relative_path] = "unsupported_yaml_dialect_or_data_schema"
            failed.discard(relative_path)
            skipped.discard(relative_path)
for node in result.get("nodes", []):
    if node.get("source_file"):
        node["source_file"] = relative(node["source_file"])
result["file_coverage"] = [{"path": p.relative_to(root).as_posix(),
    "status": "unsupported" if p.relative_to(root).as_posix() in unsupported else "error" if p.relative_to(root).as_posix() in failed | skipped else "processed" if p in supported else "unsupported",
    "reason": unsupported.get(p.relative_to(root).as_posix(), "extractor_failed_or_skipped" if p.relative_to(root).as_posix() in failed | skipped else "static_parser_with_native_semantic_limits" if p in supported else "no_static_parser")}
    for p in all_files]
result["processing_complete"] = not (failed or skipped)
output.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
