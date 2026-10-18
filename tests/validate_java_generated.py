#!/usr/bin/env python3
"""Validate emitted Java Quiz/Interview/Roadmap files with shared JSON Schemas.

Usage:
    python -m pip install jsonschema PyYAML
    python tests/validate_java_generated.py --data-dir PATH_TO_build/learning-data/java

Other generated document types will be covered by a future full-data validator.
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
KIND_AND_NAME = {
    "quiz": ("question.yml", "quiz.schema.json"),
    "interview": ("question.yml", "interview.schema.json"),
    "roadmap": ("roadmap.yml", "roadmap.schema.json"),
}


def validators():
    schema_by_name = {
        path.name: json.loads(path.read_text(encoding="utf-8"))
        for path in SCHEMAS.glob("*.schema.json")
    }
    # Schemas deliberately have no published $id yet. Supply a stable local
    # base URI only in this validator so sibling ./common.schema.json resolves.
    base = "https://learning-contract.local.invalid/schemas/"
    registry = Registry()
    for name, schema in schema_by_name.items():
        schema["$id"] = base + name
        Draft202012Validator.check_schema(schema)
        registry = registry.with_resource(base + name, Resource.from_contents(schema))
    return {
        kind: Draft202012Validator(schema_by_name[schema_name], registry=registry)
        for kind, (_, schema_name) in KIND_AND_NAME.items()
    }


def validate_data(data_dir, limit=20):
    """Return (number of files checked, failure count) and print a useful audit."""
    checks = validators()
    counts = Counter()
    failed = 0
    shown = 0
    for kind, (file_name, _) in KIND_AND_NAME.items():
        # File path: module/{routeId}/{kind}/{language}/{file_name}
        for source in sorted((data_dir / "module").glob(f"*/{kind}/*/{file_name}")):
            counts[kind] += 1
            try:
                with source.open(encoding="utf-8-sig") as handle:
                    document = yaml.safe_load(handle)
                errors = sorted(checks[kind].iter_errors(document), key=lambda e: repr(list(e.path)))
            except (ValueError, yaml.YAMLError, UnicodeError) as exc:
                errors = [exc]
            if errors:
                failed += 1
                for error in errors:
                    if shown >= limit:
                        break
                    path = ".".join(map(str, error.path)) if hasattr(error, "path") else ""
                    print(f"FAIL {source.relative_to(data_dir)} {path}: {error.message if hasattr(error, 'message') else error}")
                    shown += 1
    if not counts:
        raise ValueError(f"No Quiz/Interview/Roadmap files found under {data_dir}")
    print(f"SCHEMA AUDIT: files={sum(counts.values())}, by_type={dict(counts)}, failed_files={failed}")
    if shown >= limit:
        print(f"Only the first {limit} validation errors were displayed.")
    return sum(counts.values()), failed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True, type=Path)
    parser.add_argument("--limit", default=20, type=int)
    args = parser.parse_args()
    checked, failed = validate_data(args.data_dir, args.limit)
    return 0 if checked and not failed else 1


if __name__ == "__main__":
    sys.exit(main())
