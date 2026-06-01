import unittest

from endo_ai_assistant import (
    AnatomicalZone,
    FindingType,
    GastroscopyZone,
    ObservationType,
    OBSERVATION_LABELS,
    OBSERVATION_SYNONYMS,
    ZONE_LABELS,
    ZONE_SYNONYMS,
    export_nomenclature,
)


class NomenclatureTest(unittest.TestCase):
    def test_real_zone_labels_and_synonyms_are_available(self) -> None:
        self.assertEqual(ZONE_LABELS[AnatomicalZone.ANTRUM], "Антральный отдел")
        self.assertIn("антрум", ZONE_SYNONYMS[AnatomicalZone.ANTRUM])
        self.assertEqual(GastroscopyZone.ANTRUM.value, "antrum")

    def test_finding_type_alias_keeps_domain_name(self) -> None:
        self.assertIs(FindingType, ObservationType)
        self.assertEqual(FindingType.SUBMUCOSAL_LESION.value, "submucosal_lesion")

    def test_labels_cover_all_enum_values(self) -> None:
        self.assertEqual(set(ZONE_LABELS), set(AnatomicalZone))
        self.assertEqual(set(OBSERVATION_LABELS), set(ObservationType))

    def test_synonyms_cover_all_real_values(self) -> None:
        zones_without_synonyms = {AnatomicalZone.UNKNOWN}
        observation_types_without_synonyms = {ObservationType.OTHER}

        self.assertFalse((set(AnatomicalZone) - zones_without_synonyms) - set(ZONE_SYNONYMS))
        self.assertFalse(
            (set(ObservationType) - observation_types_without_synonyms)
            - set(OBSERVATION_SYNONYMS)
        )

    def test_export_nomenclature_groups_exam_specific_zones(self) -> None:
        exported = export_nomenclature()
        gastroscopy_codes = {
            item["code"] for item in exported["gastroscopy_zones"]
        }
        colonoscopy_codes = {
            item["code"] for item in exported["colonoscopy_zones"]
        }

        self.assertIn("antrum", gastroscopy_codes)
        self.assertNotIn("antrum", colonoscopy_codes)
        self.assertIn("rectum", colonoscopy_codes)
        self.assertNotIn("unknown", gastroscopy_codes)
        self.assertNotIn("unknown", colonoscopy_codes)
        self.assertIn("submucosal_lesion", {
            item["code"] for item in exported["finding_types"]
        })


if __name__ == "__main__":
    unittest.main()
