"""Behavioral regression tests for the gearbox requirement schema."""

from __future__ import annotations

import unittest

from pydantic import ValidationError

from schema.gearbox_requirement_schema import (
    DesignRequirement,
    QuantitativeRequirement,
    RangeValue,
    SourceReference,
    Tolerance,
)


class ValueObjectTests(unittest.TestCase):
    def test_units_paths_ranges_and_tolerances_are_normalized(self) -> None:
        self.assertEqual(RangeValue(minimum=-10, maximum=40, unit="℃").unit, "degC")
        self.assertEqual(SourceReference.model_validate("a\\b.txt").path, "a/b.txt")
        self.assertEqual(
            Tolerance(type="absolute", value=0.2, unit="毫米").unit,
            "mm",
        )

    def test_invalid_range_and_tolerance_are_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            RangeValue(minimum=2, maximum=1)
        with self.assertRaises(ValidationError):
            Tolerance(type="relative", value=0.1, unit="%")


class RequirementNormalizationTests(unittest.TestCase):
    def test_quantitative_semantics_defaults_and_locking_are_preserved(self) -> None:
        ratio = QuantitativeRequirement(name="总传动比", value=3)
        life = QuantitativeRequirement(name="使用寿命", value=10, unit="年")

        self.assertEqual(ratio.semantic_key, "total_transmission_ratio")
        self.assertEqual(ratio.unit, "dimensionless")
        self.assertEqual(ratio.qualifier, "target")
        self.assertEqual(ratio.confidence, 1.0)
        self.assertTrue(ratio.locked)
        self.assertEqual(life.semantic_key, "design_life_duration")
        self.assertEqual(life.unit, "year")
        self.assertEqual(life.qualifier, "minimum")

    def test_complete_document_normalization_is_preserved(self) -> None:
        requirement = DesignRequirement.model_validate(
            {
                "title": "单级圆柱齿轮减速器",
                "objective": "为工作机设计减速器",
                "functional_requirements": ["传递动力"],
                "quantitative_requirements": [
                    {"name": "传动比", "value": 3},
                    {"name": "使用寿命", "value": 10, "unit": "年"},
                ],
                "environmental_requirements": [
                    {
                        "statement": "温度范围 -10℃ 至 40℃",
                        "parsed_value": {
                            "minimum": -10,
                            "maximum": 40,
                            "unit": "℃",
                        },
                    }
                ],
                "lifecycle_requirements": ["便于维护"],
                "other_constraints": ["采用圆柱齿轮"],
                "assumptions": ["按连续负载设计"],
                "completeness": {"notes": ["需要说明负载曲线"]},
                "source_files": ["examples\\requirement.txt"],
            }
        )

        self.assertEqual(requirement.source_files[0].path, "examples/requirement.txt")
        self.assertEqual(
            requirement.environmental_requirements[0].semantic_key,
            "ambient_temperature",
        )
        self.assertEqual(
            requirement.environmental_requirements[0].parsed_value.unit,
            "degC",
        )
        self.assertEqual(requirement.environmental_requirements[0].qualifier, "range")
        self.assertTrue(requirement.assumptions[0].requires_confirmation)
        self.assertEqual(requirement.other_constraints[0].confidence, None)

        functional_keys = {
            item.semantic_key for item in requirement.functional_requirements
        }
        self.assertIn("speed_reduction", functional_keys)
        self.assertIn("design_life", functional_keys)
        self.assertEqual(
            requirement.unresolved_items[0].field,
            "operating_conditions.load_profile",
        )
        self.assertTrue(requirement.unresolved_items[0].blocking)
        self.assertEqual(requirement.completeness.blocking_item_count, 1)
        self.assertEqual(requirement.completeness.overall_status, "incomplete")
        self.assertTrue(requirement.extraction_id.startswith("REQ-EXT-"))

        all_ids = [
            item.id
            for field in requirement._ID_PREFIXES
            for item in getattr(requirement, field[0])
        ]
        self.assertEqual(len(all_ids), len(set(all_ids)))

    def test_duplicate_ids_across_sections_are_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            DesignRequirement.model_validate(
                {
                    "title": "Duplicate ID test",
                    "objective": "Verify uniqueness",
                    "functional_requirements": [
                        {"id": "REQ-1", "statement": "Transmit power"}
                    ],
                    "quantitative_requirements": [
                        {"id": "REQ-1", "name": "Power", "value": 10}
                    ],
                }
            )


if __name__ == "__main__":
    unittest.main()
