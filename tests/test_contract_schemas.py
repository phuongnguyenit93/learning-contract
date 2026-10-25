"""Regression tests for draft Quiz, Interview, and Roadmap JSON Schemas.

Requires: python -m pip install jsonschema PyYAML
Run: python -m unittest discover -s tests -p 'test_*.py' -v
"""

import json
import unittest

import yaml

from validate_java_generated import SCHEMAS, validators


def load_schema(name):
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def relation_defaults():
    return {
        "readmeRelated": {"file": "", "anchor": ""},
        "apiRelated": {"controller": "", "methodSignature": ""},
    }


def quiz_example():
    return {
        "questions": [{
            "id": "quiz-1",
            "question": "What is a JVM?",
            "aiGenerated": True,
            "reviewed": False,
            **relation_defaults(),
            "answers": [
                {"id": key, "answer": f"Answer {key}", "explanation": "Explanation"}
                for key in ("D", "B", "A", "C")
            ],
            "correctAnswerId": "B",
        }]
    }


def interview_example():
    return {
        "questions": [{
            "question": "Explain the JVM.",
            "answer": "It executes Java bytecode.",
            "aiGenerated": True,
            "reviewed": False,
            **relation_defaults(),
        }]
    }


def roadmap_example():
    return {
        "roadmap": [{
            "id": "foundation",
            "title": "Foundation",
            "purpose": "Build mental model",
            "objectives": ["Understand execution"],
            "relatedKnowledge": ["Basics"],
            "relatedModules": [{"routeId": "JAVA_CORE", "label": "Core"}],
        }]
    }


class ContractSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Also checks all local schemas against the Draft 2020-12 metaschema.
        cls.checks = validators()

    def assert_valid(self, kind, doc):
        errors = list(self.checks[kind].iter_errors(doc))
        self.assertEqual([], [str(e) for e in errors])

    def assert_invalid(self, kind, doc):
        self.assertTrue(list(self.checks[kind].iter_errors(doc)))

    def test_quiz_valid_four_answers_in_any_order(self):
        self.assert_valid("quiz", quiz_example())
        self.assert_valid("quiz", {"questions": []})

    def test_quiz_requires_four_distinct_answer_ids(self):
        doc = quiz_example()
        doc["questions"][0]["answers"][0]["id"] = "A"
        self.assert_invalid("quiz", doc)

    def test_quiz_rejects_missing_and_invalid_answer_ids(self):
        doc = quiz_example()
        doc["questions"][0]["answers"][0]["id"] = "E"
        self.assert_invalid("quiz", doc)
        doc = quiz_example()
        del doc["questions"][0]["correctAnswerId"]
        self.assert_invalid("quiz", doc)

    def test_quiz_nonblank_and_required(self):
        for field in ("id", "question"):
            doc = quiz_example()
            doc["questions"][0][field] = "  "
            self.assert_invalid("quiz", doc)
        doc = quiz_example()
        doc["questions"][0]["answers"][0]["explanation"] = "\n "
        self.assert_invalid("quiz", doc)

    def test_interview_nonblank_and_required(self):
        self.assert_valid("interview", interview_example())
        self.assert_valid("interview", {"questions": []})
        for field in ("question", "answer"):
            doc = interview_example()
            doc["questions"][0][field] = " "
            self.assert_invalid("interview", doc)
        doc = interview_example()
        del doc["questions"][0]["reviewed"]
        self.assert_invalid("interview", doc)

    def test_relations_require_both_fields_or_neither(self):
        for kind, example in (("quiz", quiz_example), ("interview", interview_example)):
            doc = example()
            doc["questions"][0]["readmeRelated"] = {"file": "1.Basic/knowledge/Basic.md", "anchor": "basics"}
            doc["questions"][0]["apiRelated"] = {
                "controller": "DemoController", "methodSignature": "demo()"
            }
            self.assert_valid(kind, doc)
            doc["questions"][0]["readmeRelated"]["anchor"] = ""
            self.assert_invalid(kind, doc)
            doc = example()
            doc["questions"][0]["apiRelated"]["methodSignature"] = "  "
            self.assert_invalid(kind, doc)

    def test_roadmap_optional_lists_and_related_module(self):
        self.assert_valid("roadmap", roadmap_example())
        self.assert_valid("roadmap", {"roadmap": []})
        doc = roadmap_example()
        doc["roadmap"][0]["relatedModules"][0]["routeId"] = ""
        self.assert_invalid("roadmap", doc)
        doc = roadmap_example()
        doc["roadmap"][0]["objectives"] = [{"unquoted": "YAML colon"}]
        self.assert_invalid("roadmap", doc)

    def test_roundtrip_yaml_is_accepted(self):
        for kind, example in (
            ("quiz", quiz_example), ("interview", interview_example), ("roadmap", roadmap_example)
        ):
            doc = yaml.safe_load(yaml.safe_dump(example(), allow_unicode=True))
            self.assert_valid(kind, doc)

    def test_bilingual_descriptions_and_defaults(self):
        for kind, root_key in (("quiz", "questions"), ("interview", "questions"), ("roadmap", "roadmap")):
            schema = load_schema(f"{kind}.schema.json")
            self.assertEqual({"vi", "en"}, set(schema["x-description"]))
            self.assertEqual({"vi", "en"}, set(schema["x-title"]))
            root = schema["properties"][root_key]
            self.assertEqual([], root["default"])
            self.assertEqual({"vi", "en"}, set(root["x-description"]))
            for name, definition in root["items"]["properties"].items():
                if "$ref" in definition and "x-description" not in definition and "common.schema.json" in definition["$ref"]:
                    shared_name = definition["$ref"].split("/")[-1]
                    definition = load_schema("common.schema.json")["$defs"][shared_name]
                self.assertEqual({"vi", "en"}, set(definition.get("x-description", {})),
                                 f"{kind}.{name}: missing bilingual description")
        quiz = load_schema("quiz.schema.json")
        item = quiz["properties"]["questions"]["items"]["properties"]
        self.assertEqual("", item["id"]["default"])
        self.assertEqual("", item["question"]["default"])
        self.assertTrue(item["aiGenerated"]["default"])
        self.assertFalse(item["reviewed"]["default"])
        self.assertEqual("", item["correctAnswerId"]["default"])
        self.assertEqual([], item["answers"]["default"])
        common = load_schema("common.schema.json")["$defs"]
        self.assertEqual({"file": "", "anchor": ""}, common["readmeRelation"]["default"])
        self.assertEqual({"controller": "", "methodSignature": ""},
                         common["apiRelation"]["default"])

    def test_custom_unique_annotations_and_roadmap_guidance(self):
        quiz = load_schema("quiz.schema.json")
        roadmap = load_schema("roadmap.schema.json")
        self.assertEqual("id", quiz["properties"]["questions"]["x-uniqueBy"])
        self.assertEqual("id", quiz["properties"]["questions"]["items"]["properties"]["answers"]["x-uniqueBy"])
        self.assertEqual("id", roadmap["properties"]["roadmap"]["x-uniqueBy"])
        self.assertEqual(9, len(roadmap["x-guidance"]["thinkingFramework"]))
        self.assertEqual({"ownership", "order", "flexibility"},
                         set(roadmap["x-guidance"]["principles"]))

    def test_defaults_are_annotations_not_auto_population(self):
        doc = quiz_example()
        del doc["questions"][0]["reviewed"]
        self.assert_invalid("quiz", doc)

    def test_knowledge_importance_is_optional_boolean_default_false(self):
        from jsonschema import Draft202012Validator
        section = load_schema("knowledge.schema.json")["$defs"]["section"]
        flag = section["properties"]["isImportant"]
        self.assertEqual("boolean", flag["type"])
        self.assertIs(flag["default"], False)
        self.assertNotIn("isImportant", section["required"])
        self.assertFalse(list(Draft202012Validator(flag).iter_errors(True)))
        self.assertFalse(list(Draft202012Validator(flag).iter_errors(False)))
        self.assertTrue(list(Draft202012Validator(flag).iter_errors("true")))


if __name__ == "__main__":
    unittest.main()
