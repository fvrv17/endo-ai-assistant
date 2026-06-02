from __future__ import annotations

from enum import Enum
from typing import Dict, FrozenSet, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class EndoscopyType(str, Enum):
    GASTROSCOPY = "gastroscopy"
    COLONOSCOPY = "colonoscopy"


class AnatomicalZone(str, Enum):
    ESOPHAGUS = "esophagus"
    UPPER_ESOPHAGUS = "upper_esophagus"
    MIDDLE_ESOPHAGUS = "middle_esophagus"
    LOWER_ESOPHAGUS = "lower_esophagus"
    Z_LINE = "z_line"
    GE_JUNCTION = "ge_junction"
    CARDIA = "cardia"
    FUNDUS = "fundus"
    GASTRIC_BODY = "gastric_body"
    UPPER_STOMACH = "upper_stomach"
    MIDDLE_STOMACH = "middle_stomach"
    LOWER_STOMACH = "lower_stomach"
    LESSER_CURVATURE = "lesser_curvature"
    GREATER_CURVATURE = "greater_curvature"
    INCISURA = "incisura"
    ANTRUM = "antrum"
    PYLORUS = "pylorus"
    DUODENAL_BULB = "duodenal_bulb"
    DUODENUM_D2 = "duodenum_d2"
    DUODENUM_UNSPECIFIED = "duodenum_unspecified"
    STOMACH_UNSPECIFIED = "stomach_unspecified"
    UPPER_GI_UNSPECIFIED = "upper_gi_unspecified"
    PERIANAL = "perianal"
    ANAL_CANAL = "anal_canal"
    RECTUM = "rectum"
    RECTOSIGMOID = "rectosigmoid"
    SIGMOID_COLON = "sigmoid_colon"
    DESCENDING_COLON = "descending_colon"
    SPLENIC_FLEXURE = "splenic_flexure"
    TRANSVERSE_COLON = "transverse_colon"
    HEPATIC_FLEXURE = "hepatic_flexure"
    ASCENDING_COLON = "ascending_colon"
    CECUM = "cecum"
    CECAL_POLE = "cecal_pole"
    APPENDICEAL_ORIFICE = "appendiceal_orifice"
    ILEOCECAL_VALVE = "ileocecal_valve"
    TERMINAL_ILEUM = "terminal_ileum"
    COLON_UNSPECIFIED = "colon_unspecified"
    LARGE_BOWEL_UNSPECIFIED = "large_bowel_unspecified"
    LEFT_COLON = "left_colon"
    RIGHT_COLON = "right_colon"
    UNKNOWN = "unknown"


class ObservationType(str, Enum):
    NORMAL = "normal"
    POLYP = "polyp"
    MASS = "mass"
    TUMOR = "tumor"
    SUBMUCOSAL_LESION = "submucosal_lesion"
    EROSION = "erosion"
    ULCER = "ulcer"
    APHTHA = "aphtha"
    ERYTHEMA = "erythema"
    INFLAMMATION = "inflammation"
    EDEMA = "edema"
    GRANULARITY = "granularity"
    FRIABILITY = "friability"
    CONTACT_BLEEDING = "contact_bleeding"
    BLEEDING = "bleeding"
    BLOOD_IN_LUMEN = "blood_in_lumen"
    HEMORRHAGE = "hemorrhage"
    VASCULAR_ECTASIA = "vascular_ectasia"
    DIVERTICULUM = "diverticulum"
    STENOSIS = "stenosis"
    DEFORMITY = "deformity"
    SCAR = "scar"
    ATROPHY = "atrophy"
    METAPLASIA = "metaplasia"
    SUSPECTED_DYSPLASIA = "suspected_dysplasia"
    SUSPECTED_BARRETT = "suspected_barrett"
    ESOPHAGITIS = "esophagitis"
    HIATAL_HERNIA = "hiatal_hernia"
    VARICES = "varices"
    CANDIDIASIS = "candidiasis"
    GASTRITIS = "gastritis"
    GASTROPATHY = "gastropathy"
    DUODENITIS = "duodenitis"
    BULBITIS = "bulbitis"
    BILE_REFLUX = "bile_reflux"
    RETAINED_CONTENT = "retained_content"
    FOREIGN_BODY = "foreign_body"
    COLITIS = "colitis"
    PROCTITIS = "proctitis"
    ILEITIS = "ileitis"
    PSEUDOMEMBRANES = "pseudomembranes"
    MELANOSIS_COLI = "melanosis_coli"
    HEMORRHOIDS = "hemorrhoids"
    ANAL_FISSURE = "anal_fissure"
    FISTULA = "fistula"
    POOR_PREP = "poor_prep"
    STOOL_RESIDUE = "stool_residue"
    BIOPSY_TAKEN = "biopsy_taken"
    RESECTION_PERFORMED = "resection_performed"
    OTHER = "other"


FindingType = ObservationType


GASTROSCOPY_ZONES: FrozenSet[AnatomicalZone] = frozenset(
    {
        AnatomicalZone.ESOPHAGUS,
        AnatomicalZone.UPPER_ESOPHAGUS,
        AnatomicalZone.MIDDLE_ESOPHAGUS,
        AnatomicalZone.LOWER_ESOPHAGUS,
        AnatomicalZone.Z_LINE,
        AnatomicalZone.GE_JUNCTION,
        AnatomicalZone.CARDIA,
        AnatomicalZone.FUNDUS,
        AnatomicalZone.GASTRIC_BODY,
        AnatomicalZone.UPPER_STOMACH,
        AnatomicalZone.MIDDLE_STOMACH,
        AnatomicalZone.LOWER_STOMACH,
        AnatomicalZone.LESSER_CURVATURE,
        AnatomicalZone.GREATER_CURVATURE,
        AnatomicalZone.INCISURA,
        AnatomicalZone.ANTRUM,
        AnatomicalZone.PYLORUS,
        AnatomicalZone.DUODENAL_BULB,
        AnatomicalZone.DUODENUM_D2,
        AnatomicalZone.DUODENUM_UNSPECIFIED,
        AnatomicalZone.STOMACH_UNSPECIFIED,
        AnatomicalZone.UPPER_GI_UNSPECIFIED,
    }
)

COLONOSCOPY_ZONES: FrozenSet[AnatomicalZone] = frozenset(
    {
        AnatomicalZone.TERMINAL_ILEUM,
        AnatomicalZone.CECUM,
        AnatomicalZone.CECAL_POLE,
        AnatomicalZone.APPENDICEAL_ORIFICE,
        AnatomicalZone.ILEOCECAL_VALVE,
        AnatomicalZone.ASCENDING_COLON,
        AnatomicalZone.HEPATIC_FLEXURE,
        AnatomicalZone.TRANSVERSE_COLON,
        AnatomicalZone.SPLENIC_FLEXURE,
        AnatomicalZone.DESCENDING_COLON,
        AnatomicalZone.SIGMOID_COLON,
        AnatomicalZone.RECTOSIGMOID,
        AnatomicalZone.RECTUM,
        AnatomicalZone.ANAL_CANAL,
        AnatomicalZone.PERIANAL,
        AnatomicalZone.COLON_UNSPECIFIED,
        AnatomicalZone.LARGE_BOWEL_UNSPECIFIED,
        AnatomicalZone.LEFT_COLON,
        AnatomicalZone.RIGHT_COLON,
    }
)

ZONES_BY_EXAM_TYPE: Dict[EndoscopyType, FrozenSet[AnatomicalZone]] = {
    EndoscopyType.GASTROSCOPY: GASTROSCOPY_ZONES,
    EndoscopyType.COLONOSCOPY: COLONOSCOPY_ZONES,
}


class Observation(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    type: ObservationType
    description: str = Field(min_length=1)
    location: Optional[str] = None
    size_mm: Optional[float] = None
    quantity: Optional[int] = None
    evidence_text: str = Field(
        min_length=1,
        description="Short source fragment from the doctor's input that supports this observation.",
    )

    @field_validator("description", "evidence_text")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("field cannot be empty")
        return value

    @field_validator("location")
    @classmethod
    def strip_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("size_mm")
    @classmethod
    def size_must_be_plausible(cls, value: Optional[float]) -> Optional[float]:
        if value is None:
            return None
        if value <= 0:
            raise ValueError("size_mm must be greater than 0 when provided")
        if value > 300:
            raise ValueError("size_mm is outside a plausible endoscopic range")
        return value

    @field_validator("quantity")
    @classmethod
    def quantity_must_be_positive(cls, value: Optional[int]) -> Optional[int]:
        if value is None:
            return None
        if value <= 0:
            raise ValueError("quantity must be greater than 0 when provided")
        return value


class ZoneFinding(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    zone: AnatomicalZone
    observations: List[Observation]


class ExtractedFindings(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    findings: List[ZoneFinding]


class EndoscopyReport(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    exam_type: EndoscopyType
    raw_input: str = Field(min_length=1)
    indication: Optional[str] = None
    findings: List[ZoneFinding] = Field(default_factory=list)

    @field_validator("raw_input")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("field cannot be empty")
        return value

    @field_validator("indication")
    @classmethod
    def strip_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @model_validator(mode="after")
    def validate_report_consistency(self) -> EndoscopyReport:
        allowed_zones = ZONES_BY_EXAM_TYPE[self.exam_type]
        source = self.raw_input.lower()
        for zone in self.findings:
            if zone.zone not in allowed_zones:
                raise ValueError(
                    f"zone {zone.zone.value} is not allowed for {self.exam_type.value}"
                )
            for observation in zone.observations:
                # Intentionally coarse first barrier: this catches many facts that
                # are not grounded in the source, but it is not full span grounding.
                # Known gaps: negated mentions still match, and punctuation/casing
                # normalization can reject semantically valid evidence. The next
                # step is span offsets plus a dedicated negation check.
                evidence = observation.evidence_text.lower()
                if evidence not in source:
                    raise ValueError(
                        "every observation.evidence_text must be traceable to raw_input"
                    )
        return self
