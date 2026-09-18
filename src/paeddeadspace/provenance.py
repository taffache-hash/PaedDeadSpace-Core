"""Structured provenance for scientific equations, boundaries, and presets."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ParameterClassification(str, Enum):
    MEASURED_EMPIRICAL = "measured/empirical"
    DERIVED = "derived"
    ASSUMPTION = "assumption"
    USER_DEFINED = "user-defined"


@dataclass(frozen=True, slots=True)
class EvidenceSource:
    """A contextual evidence source that does not change classification."""

    source_id: str
    citation: str
    context: str
    doi: str | None = None

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("evidence source_id must not be empty")
        if not self.citation.strip():
            raise ValueError("evidence citation must not be empty")
        if not self.context.strip():
            raise ValueError("evidence context must not be empty")


@dataclass(frozen=True, slots=True)
class Provenance:
    classification: ParameterClassification
    source_id: str
    citation: str
    context: str
    doi: str | None = None
    evidence_sources: tuple[EvidenceSource, ...] = ()

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("provenance source_id must not be empty")
        if not self.citation.strip():
            raise ValueError("provenance citation must not be empty")
        if not self.context.strip():
            raise ValueError("provenance context must not be empty")


@dataclass(frozen=True, slots=True)
class NamedConstant:
    name: str
    value: float
    unit: str
    provenance: Provenance


@dataclass(frozen=True, slots=True)
class EquationProvenance:
    equation_id: str
    formula: str
    provenance: Provenance
    constants: tuple[NamedConstant, ...]


ENGINE_SPEC_PROVENANCE = Provenance(
    classification=ParameterClassification.ASSUMPTION,
    source_id="ENGINE_SPEC_V1_0_0",
    citation="PaedDeadSpace v1.0.0 model architecture",
    context="Audited project specification; values are not therapeutic defaults.",
)

NUMA_1996 = Provenance(
    classification=ParameterClassification.MEASURED_EMPIRICAL,
    source_id="NUMA_1996_TOTAL_ANATOMIC_DS",
    citation="Numa et al., Journal of Applied Physiology, 1996",
    context=(
        "Total anatomic dead-space age scaling, not intubated physiologic VD. "
        "Extrathoracic measurements covered ages 7 days–14.2 years; "
        "intrathoracic measurements covered 18 days–14.7 years. The common "
        "non-extrapolated overlap for a total reference is 18 days–14.2 years."
    ),
    doi="10.1152/jappl.1996.80.5.1485",
)

NUMA_INTRATHORACIC_1996 = Provenance(
    classification=ParameterClassification.MEASURED_EMPIRICAL,
    source_id="NUMA_1996_MEAN_INTRATHORACIC_ANATOMIC_DS",
    citation="Numa and Newth, Journal of Applied Physiology, 1996",
    context=(
        "Measured empirical source component: mean intrathoracic anatomic "
        "dead space approximately 1.03 mL/kg. Intrathoracic measurements "
        "covered approximately 18 days–14.7 years. This observation alone is "
        "not a universal intubated-pediatric physiologic dead-space default."
    ),
    doi="10.1152/jappl.1996.80.5.1485",
)

FLETCHER_1986 = Provenance(
    classification=ParameterClassification.MEASURED_EMPIRICAL,
    source_id="FLETCHER_1986_ALVEOLAR_DS_FRACTION",
    citation=(
        "Fletcher, Niklason and Drefeldt, Anesthesia & Analgesia, 1986"
    ),
    context=(
        "Measured empirical source component: mean VDalv/VTalv was 0.10 in "
        "the subgroup of children with normal pulmonary circulation during "
        "anesthesia and controlled ventilation before thoracic surgery. The "
        "overall study included 42 children and corrected apparatus dead "
        "space, compression and rebreathing online. Normal pulmonary "
        "circulation is not equivalent to a healthy source population, and "
        "the value is not a universal pediatric alveolar-dead-space fraction."
    ),
    doi="10.1213/00000539-198606000-00014",
)

NUMA_COMPONENT_EVIDENCE = EvidenceSource(
    source_id=NUMA_INTRATHORACIC_1996.source_id,
    citation=NUMA_INTRATHORACIC_1996.citation,
    context=NUMA_INTRATHORACIC_1996.context,
    doi=NUMA_INTRATHORACIC_1996.doi,
)

FLETCHER_COMPONENT_EVIDENCE = EvidenceSource(
    source_id=FLETCHER_1986.source_id,
    citation=FLETCHER_1986.citation,
    context=FLETCHER_1986.context,
    doi=FLETCHER_1986.doi,
)

HEALTHY_INTUBATED_COMPOSITE_CONSTRUCTION = Provenance(
    classification=ParameterClassification.ASSUMPTION,
    source_id="PAEDDEADSPACE_NUMA_FLETCHER_COMPOSITE_CONSTRUCTION",
    citation="PaedDeadSpace v1.0.0 model construction",
    context=(
        "Assumption/model construction combining the Numa mean "
        "intrathoracic anatomic component with the Fletcher mean alveolar "
        "dead-space fraction. The exact combined equation was not directly "
        "published or validated as a single equation in either source. It is "
        "a sensitivity/reference mode, not a clinical or universal default; "
        "apparatus dead space is excluded and remains separately entered."
    ),
    evidence_sources=(NUMA_COMPONENT_EVIDENCE, FLETCHER_COMPONENT_EVIDENCE),
)

WILLIAMS_TERM_CONTROL_2022 = Provenance(
    classification=ParameterClassification.MEASURED_EMPIRICAL,
    source_id="WILLIAMS_2022_TERM_CONTROL_TABLE_2",
    citation="Williams et al., Pediatric Research, 2022; online 2021",
    context=(
        "Descriptive term-control cohort medians and IQRs from Table 2. The "
        "controls were term infants without underlying respiratory disease "
        "who nevertheless required invasive ventilation for poor perinatal "
        "adaptation; this is not a generic healthy-neonate cohort. These group "
        "summaries support plausibility and validation context only. Medians "
        "and IQRs of different variables are not algebraically decomposable "
        "into an individual patient-only dead-space value."
    ),
    doi="10.1038/s41390-021-01388-8",
)

LINDAHL_BJA_1989 = Provenance(
    classification=ParameterClassification.MEASURED_EMPIRICAL,
    source_id="LINDAHL_BJA_1989_VCO2",
    citation="Lindahl, British Journal of Anaesthesia, 1989",
    context=(
        "Carbon dioxide elimination measured in 38 anesthetized infants and "
        "children (3.6–25 kg). Four children weighing <5 kg with congenital "
        "heart malformations were studied during controlled mechanical "
        "ventilation; the remaining 34 healthy children breathed "
        "spontaneously. The pooled regression was VCO2=4.8*weight_kg+6.4 "
        "(r=0.94). Transportability to a fully mechanically ventilated "
        "population is not established by this equation alone."
    ),
    doi="10.1093/bja/62.1.70",
)

LINDAHL_CJA_1989 = Provenance(
    classification=ParameterClassification.MEASURED_EMPIRICAL,
    source_id="LINDAHL_CJA_1989_VCO2",
    citation="Lindahl et al., Canadian Journal of Anaesthesia, 1989",
    context=(
        "Spontaneously breathing anesthetized infants/children; reported "
        "weight range 2.8–26.5 kg."
    ),
    doi="10.1007/BF03011430",
)

PEARSALL_2014 = Provenance(
    classification=ParameterClassification.ASSUMPTION,
    source_id="PEARSALL_2014_BRODY_INHERITED_BENCHMARK",
    citation="Pearsall et al., Anesthesia & Analgesia, 2014; Brody equation",
    context=(
        "Assumption inherited from the prior model/benchmark, not a modern "
        "measured empirical default. Named benchmark context only: ages 0–36 "
        "months, weights 2–17 kg, VT 8 mL/kg, patient physiologic VD/VT 0.30 "
        "excluding apparatus, RR 20/min, and VCO2=5.56*weight_kg**1.05."
    ),
    doi="10.1213/ANE.0000000000000148",
)

PEARSALL_BENCHMARK_ASSUMPTION = Provenance(
    classification=ParameterClassification.ASSUMPTION,
    source_id="PEARSALL_2014_PATIENT_VD_VT_BENCHMARK_ASSUMPTION",
    citation="Pearsall et al., Anesthesia & Analgesia, 2014",
    context=(
        "Named benchmark patient physiologic VD/VT assumption of 0.30, "
        "explicitly excluding separately entered apparatus dead space; not a "
        "universal patient default. Benchmark context: 0–36 months, 2–17 kg, "
        "VT 8 mL/kg, and RR 20/min."
    ),
    doi="10.1213/ANE.0000000000000148",
)

SPAETH_2022 = EvidenceSource(
    source_id="SPAETH_2022_VT_CONTEXT",
    citation="Spaeth et al., Paediatric Anaesthesia, 2022",
    context=(
        "Evidence context for pediatric perioperative tidal-volume selection "
        "and age-dependent interpretation; not a source of a universal "
        "clinical default."
    ),
    doi="10.1111/pan.14366",
)

FELDMAN_2015 = EvidenceSource(
    source_id="FELDMAN_2015_VT_CONTEXT",
    citation="Feldman, Anesthesia & Analgesia, 2015",
    context=(
        "Evidence context for lung-protective and historical perioperative "
        "ventilation comparisons; not a source of a universal clinical default."
    ),
    doi="10.1213/ANE.0000000000000472",
)

NUMA_TOTAL_ANATOMIC_INTERCEPT = NamedConstant(
    "numa_total_anatomic_intercept", 3.28, "mL/kg", NUMA_1996
)
NUMA_LOG_COEFFICIENT = NamedConstant(
    "numa_log_coefficient", 0.56, "mL/kg", NUMA_1996
)
NUMA_AGE_OFFSET_YEARS = NamedConstant(
    "numa_age_offset_years", 1.0, "year", NUMA_1996
)
NUMA_EXTRATHORACIC_MIN_AGE_YEARS = NamedConstant(
    "numa_extrathoracic_source_min_age",
    7.0 / 365.25,
    "year (7 days using 365.25 days/year)",
    NUMA_1996,
)
NUMA_EXTRATHORACIC_MAX_AGE_YEARS = NamedConstant(
    "numa_extrathoracic_source_max_age", 14.2, "year", NUMA_1996
)
NUMA_INTRATHORACIC_MIN_AGE_YEARS = NamedConstant(
    "numa_intrathoracic_source_min_age",
    18.0 / 365.25,
    "year (18 days using 365.25 days/year)",
    NUMA_1996,
)
NUMA_INTRATHORACIC_MAX_AGE_YEARS = NamedConstant(
    "numa_intrathoracic_source_max_age", 14.7, "year", NUMA_1996
)
NUMA_TOTAL_ANATOMIC_SCALING = EquationProvenance(
    equation_id="numa_1996_total_anatomic_dead_space",
    formula="mL/kg = 3.28 - 0.56 * ln(1 + age_years)",
    provenance=NUMA_1996,
    constants=(
        NUMA_TOTAL_ANATOMIC_INTERCEPT,
        NUMA_LOG_COEFFICIENT,
        NUMA_AGE_OFFSET_YEARS,
        NUMA_EXTRATHORACIC_MIN_AGE_YEARS,
        NUMA_EXTRATHORACIC_MAX_AGE_YEARS,
        NUMA_INTRATHORACIC_MIN_AGE_YEARS,
        NUMA_INTRATHORACIC_MAX_AGE_YEARS,
    ),
)

NUMA_INTRATHORACIC_DEAD_SPACE_ML_KG = NamedConstant(
    "numa_mean_intrathoracic_anatomic_dead_space",
    1.03,
    "mL/kg",
    NUMA_INTRATHORACIC_1996,
)
NUMA_INTRATHORACIC_MEAN_REFERENCE = EquationProvenance(
    equation_id="numa_1996_mean_intrathoracic_component",
    formula="airway_ds_ml = 1.03 * weight_kg",
    provenance=NUMA_INTRATHORACIC_1996,
    constants=(NUMA_INTRATHORACIC_DEAD_SPACE_ML_KG,),
)

FLETCHER_ALVEOLAR_DEAD_SPACE_FRACTION = NamedConstant(
    "fletcher_mean_alveolar_dead_space_fraction",
    0.10,
    "VDalv/VTalv",
    FLETCHER_1986,
)
FLETCHER_ALVEOLAR_FRACTION_REFERENCE = EquationProvenance(
    equation_id="fletcher_1986_mean_alveolar_fraction_component",
    formula="alveolar_ds_ml = 0.10 * alveolar_tidal_volume_ml",
    provenance=FLETCHER_1986,
    constants=(FLETCHER_ALVEOLAR_DEAD_SPACE_FRACTION,),
)

HEALTHY_INTUBATED_COMPOSITE_REFERENCE_EQUATION = EquationProvenance(
    equation_id="numa_fletcher_composite_reference",
    formula=(
        "airway_ds_ml=1.03*weight_kg; "
        "alveolar_tidal_volume_ml=vt_ml-airway_ds_ml; "
        "alveolar_ds_ml=0.10*alveolar_tidal_volume_ml; "
        "patient_vd_ml=airway_ds_ml+alveolar_ds_ml"
    ),
    provenance=HEALTHY_INTUBATED_COMPOSITE_CONSTRUCTION,
    constants=(
        NUMA_INTRATHORACIC_DEAD_SPACE_ML_KG,
        FLETCHER_ALVEOLAR_DEAD_SPACE_FRACTION,
    ),
)

LINDAHL_BJA_SLOPE = NamedConstant(
    "lindahl_bja_weight_slope", 4.8, "mL/min/kg", LINDAHL_BJA_1989
)
LINDAHL_BJA_INTERCEPT = NamedConstant(
    "lindahl_bja_intercept", 6.4, "mL/min", LINDAHL_BJA_1989
)
LINDAHL_BJA_MIN_WEIGHT_KG = NamedConstant(
    "lindahl_bja_source_min_weight", 3.6, "kg", LINDAHL_BJA_1989
)
LINDAHL_BJA_MAX_WEIGHT_KG = NamedConstant(
    "lindahl_bja_source_max_weight", 25.0, "kg", LINDAHL_BJA_1989
)
LINDAHL_BJA_VCO2 = EquationProvenance(
    equation_id="lindahl_bja_1989_vco2",
    formula="VCO2_mL_min = 4.8 * weight_kg + 6.4",
    provenance=LINDAHL_BJA_1989,
    constants=(
        LINDAHL_BJA_SLOPE,
        LINDAHL_BJA_INTERCEPT,
        LINDAHL_BJA_MIN_WEIGHT_KG,
        LINDAHL_BJA_MAX_WEIGHT_KG,
    ),
)

LINDAHL_CJA_LINEAR = NamedConstant(
    "lindahl_cja_log_linear", -1.25, "mL/min", LINDAHL_CJA_1989
)
LINDAHL_CJA_QUADRATIC = NamedConstant(
    "lindahl_cja_log_quadratic", 13.0, "mL/min", LINDAHL_CJA_1989
)
LINDAHL_CJA_MIN_WEIGHT_KG = NamedConstant(
    "lindahl_cja_source_min_weight", 2.8, "kg", LINDAHL_CJA_1989
)
LINDAHL_CJA_MAX_WEIGHT_KG = NamedConstant(
    "lindahl_cja_source_max_weight", 26.5, "kg", LINDAHL_CJA_1989
)
LINDAHL_CJA_VCO2 = EquationProvenance(
    equation_id="lindahl_cja_1989_vco2",
    formula="X=ln(weight_kg); VCO2_mL_min=-1.25*X+13.0*X**2",
    provenance=LINDAHL_CJA_1989,
    constants=(
        LINDAHL_CJA_LINEAR,
        LINDAHL_CJA_QUADRATIC,
        LINDAHL_CJA_MIN_WEIGHT_KG,
        LINDAHL_CJA_MAX_WEIGHT_KG,
    ),
)

PEARSALL_BRODY_COEFFICIENT = NamedConstant(
    "pearsall_brody_coefficient", 5.56, "mL/min", PEARSALL_2014
)
PEARSALL_BRODY_EXPONENT = NamedConstant(
    "pearsall_brody_weight_exponent", 1.05, "dimensionless", PEARSALL_2014
)
PEARSALL_MIN_WEIGHT_KG = NamedConstant(
    "pearsall_context_min_weight", 2.0, "kg", PEARSALL_2014
)
PEARSALL_MAX_WEIGHT_KG = NamedConstant(
    "pearsall_context_max_weight", 17.0, "kg", PEARSALL_2014
)
PEARSALL_MIN_AGE_YEARS = NamedConstant(
    "pearsall_context_min_age", 0.0, "year", PEARSALL_2014
)
PEARSALL_MAX_AGE_YEARS = NamedConstant(
    "pearsall_context_max_age", 3.0, "year", PEARSALL_2014
)
PEARSALL_BRODY_VCO2 = EquationProvenance(
    equation_id="pearsall_brody_named_benchmark_vco2",
    formula="VCO2_mL_min = 5.56 * weight_kg**1.05",
    provenance=PEARSALL_2014,
    constants=(
        PEARSALL_BRODY_COEFFICIENT,
        PEARSALL_BRODY_EXPONENT,
        PEARSALL_MIN_WEIGHT_KG,
        PEARSALL_MAX_WEIGHT_KG,
        PEARSALL_MIN_AGE_YEARS,
        PEARSALL_MAX_AGE_YEARS,
    ),
)
PEARSALL_VD_VT_BENCHMARK = NamedConstant(
    "pearsall_benchmark_patient_vd_vt_excluding_apparatus",
    0.30,
    "dimensionless",
    PEARSALL_BENCHMARK_ASSUMPTION,
)


def _vt_preset_provenance(value: float) -> Provenance:
    if value == 4.0:
        value_context = (
            "4 mL/kg is a low-VT sensitivity/stress-test except for "
            "age-appropriate neonatal use."
        )
    elif value == 10.0:
        value_context = "10 mL/kg is retained only as a historical comparator."
    else:
        value_context = (
            f"{value:g} mL/kg is retained as an exploratory selectable value."
        )
    return Provenance(
        classification=ParameterClassification.USER_DEFINED,
        source_id=f"USER_SELECTED_VT_PRESET_{value:g}_ML_KG",
        citation="User-selected PaedDeadSpace exploratory VT preset catalog",
        context=(
            f"{value_context} Selection remains user-defined and is neither a "
            "clinical default nor a recommendation. Evidence citations provide "
            "context only."
        ),
        evidence_sources=(SPAETH_2022, FELDMAN_2015),
    )


VT_PRESETS_ML_KG = tuple(
    NamedConstant(
        f"vt_preset_{value:g}_ml_kg",
        value,
        "mL/kg",
        _vt_preset_provenance(value),
    )
    for value in (4.0, 5.0, 6.0, 8.0, 10.0)
)

# Only measured/empirical source equations or observations belong here.
EMPIRICAL_EQUATIONS = (
    NUMA_TOTAL_ANATOMIC_SCALING,
    NUMA_INTRATHORACIC_MEAN_REFERENCE,
    FLETCHER_ALVEOLAR_FRACTION_REFERENCE,
    LINDAHL_BJA_VCO2,
    LINDAHL_CJA_VCO2,
)

# Inherited assumptions remain separately identifiable as named benchmarks.
BENCHMARK_EQUATIONS = (PEARSALL_BRODY_VCO2,)

# Model constructions retain a separate classification and collection.
MODEL_CONSTRUCTION_EQUATIONS = (
    HEALTHY_INTUBATED_COMPOSITE_REFERENCE_EQUATION,
)

SCIENTIFIC_EQUATIONS = (
    EMPIRICAL_EQUATIONS
    + BENCHMARK_EQUATIONS
    + MODEL_CONSTRUCTION_EQUATIONS
)
