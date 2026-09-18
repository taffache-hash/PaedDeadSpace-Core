"""Pure mathematical functions for the PaedDeadSpace v1.0.0 core."""

from __future__ import annotations

import math
import warnings
from collections.abc import Iterable

from .models import (
    ApparatusComponent,
    NumaFletcherCompositeComponents,
    NumaFletcherCompositeReference,
    InputValidationError,
    NonPhysicalStateError,
    NumaTotalAnatomicDeadSpaceReference,
    PatientDeadSpaceModel,
    PearsallBenchmarkPatientDeadSpace,
    SourceDomainWarning,
    UserDefinedPatientVdVt,
    VentilationInputs,
    VentilationState,
)
from .provenance import (
    FLETCHER_ALVEOLAR_DEAD_SPACE_FRACTION,
    HEALTHY_INTUBATED_COMPOSITE_REFERENCE_EQUATION,
    LINDAHL_BJA_INTERCEPT,
    LINDAHL_BJA_MAX_WEIGHT_KG,
    LINDAHL_BJA_MIN_WEIGHT_KG,
    LINDAHL_BJA_SLOPE,
    LINDAHL_CJA_LINEAR,
    LINDAHL_CJA_MAX_WEIGHT_KG,
    LINDAHL_CJA_MIN_WEIGHT_KG,
    LINDAHL_CJA_QUADRATIC,
    NUMA_AGE_OFFSET_YEARS,
    NUMA_EXTRATHORACIC_MAX_AGE_YEARS,
    NUMA_EXTRATHORACIC_MIN_AGE_YEARS,
    NUMA_INTRATHORACIC_DEAD_SPACE_ML_KG,
    NUMA_INTRATHORACIC_MAX_AGE_YEARS,
    NUMA_INTRATHORACIC_MIN_AGE_YEARS,
    NUMA_LOG_COEFFICIENT,
    NUMA_TOTAL_ANATOMIC_INTERCEPT,
    NUMA_TOTAL_ANATOMIC_SCALING,
    PEARSALL_BRODY_COEFFICIENT,
    PEARSALL_BRODY_EXPONENT,
    PEARSALL_MAX_AGE_YEARS,
    PEARSALL_MAX_WEIGHT_KG,
    PEARSALL_MIN_AGE_YEARS,
    PEARSALL_MIN_WEIGHT_KG,
    PEARSALL_VD_VT_BENCHMARK,
)


def _require_finite(name: str, value: float) -> None:
    if not math.isfinite(value):
        raise InputValidationError(f"{name} must be finite")


def _require_positive(name: str, value: float) -> None:
    _require_finite(name, value)
    if value <= 0.0:
        raise InputValidationError(f"{name} must be > 0")


def _require_nonnegative(name: str, value: float) -> None:
    _require_finite(name, value)
    if value < 0.0:
        raise InputValidationError(f"{name} must be >= 0")


def _require_physical_dead_space(vt_ml: float, vd_ml: float) -> None:
    _require_positive("vt_ml", vt_ml)
    _require_nonnegative("vd_ml", vd_ml)
    if vd_ml >= vt_ml:
        raise NonPhysicalStateError(
            f"one-compartment model breakdown: VD ({vd_ml:g} mL) "
            f"must be less than VT ({vt_ml:g} mL)"
        )


def _warn_pearsall_context(weight_kg: float, age_years: float) -> None:
    if not (
        PEARSALL_MIN_WEIGHT_KG.value
        <= weight_kg
        <= PEARSALL_MAX_WEIGHT_KG.value
        and PEARSALL_MIN_AGE_YEARS.value
        <= age_years
        <= PEARSALL_MAX_AGE_YEARS.value
    ):
        warnings.warn(
            "input is outside the Pearsall named benchmark context "
            "(0–36 months and 2–17 kg); the warning does not validate "
            "extrapolation",
            SourceDomainWarning,
            stacklevel=3,
        )


def _warn_numa_intrathoracic_context(age_years: float) -> None:
    if not (
        NUMA_INTRATHORACIC_MIN_AGE_YEARS.value
        <= age_years
        <= NUMA_INTRATHORACIC_MAX_AGE_YEARS.value
    ):
        warnings.warn(
            "the Numa intrathoracic component is outside its approximate "
            "source age range of 18 days–14.7 years; extrapolation is not "
            "validation",
            SourceDomainWarning,
            stacklevel=3,
        )


def calculate_tidal_volume_ml(
    weight_kg: float,
    *,
    vt_ml_kg: float | None = None,
    vt_ml: float | None = None,
) -> float:
    """Resolve VT from exactly one user-defined entry method."""
    _require_positive("weight_kg", weight_kg)
    if (vt_ml_kg is None) == (vt_ml is None):
        raise InputValidationError("provide exactly one of vt_ml_kg or vt_ml")
    if vt_ml_kg is not None:
        _require_positive("vt_ml_kg", vt_ml_kg)
        result = weight_kg * vt_ml_kg
    else:
        assert vt_ml is not None
        _require_positive("vt_ml", vt_ml)
        result = vt_ml
    _require_positive("calculated vt_ml", result)
    return result


def apparatus_stack_dead_space_ml(
    components: Iterable[ApparatusComponent],
) -> float:
    """Sum dead-space entries for active apparatus components only."""
    total = math.fsum(
        component.dead_space_ml for component in components if component.active
    )
    _require_nonnegative("apparatus stack dead space", total)
    return total


def numa_fletcher_composite_reference(
    weight_kg: float,
    age_years: float,
    vt_ml: float,
) -> NumaFletcherCompositeComponents:
    """Evaluate the Numa/Fletcher patient-only reference construction.

    This combines separate empirical source components. The combined equation
    is an assumption/model construction and was not directly published or
    validated as a single equation. Fletcher's 0.10 component is tied to the
    normal-pulmonary-circulation subgroup of a thoracic-surgery cohort; it is
    not evidence for a universally healthy pediatric baseline. Apparatus dead
    space is not included.
    """
    _require_positive("weight_kg", weight_kg)
    _require_nonnegative("age_years", age_years)
    _require_positive("vt_ml", vt_ml)
    _warn_numa_intrathoracic_context(age_years)

    airway_ds_ml = NUMA_INTRATHORACIC_DEAD_SPACE_ML_KG.value * weight_kg
    if vt_ml <= airway_ds_ml:
        raise NonPhysicalStateError(
            "NumaFletcherCompositeReference is nonphysical: VT "
            f"({vt_ml:g} mL) must be greater than the intrathoracic airway "
            f"component ({airway_ds_ml:g} mL)"
        )

    alveolar_tidal_volume = vt_ml - airway_ds_ml
    alveolar_ds_ml = (
        FLETCHER_ALVEOLAR_DEAD_SPACE_FRACTION.value * alveolar_tidal_volume
    )
    patient_vd_ml = airway_ds_ml + alveolar_ds_ml
    return NumaFletcherCompositeComponents(
        airway_ds_ml=airway_ds_ml,
        alveolar_tidal_volume_ml=alveolar_tidal_volume,
        alveolar_ds_ml=alveolar_ds_ml,
        patient_vd_ml_excluding_apparatus=patient_vd_ml,
        patient_vd_vt_excluding_apparatus=patient_vd_ml / vt_ml,
        provenance=HEALTHY_INTUBATED_COMPOSITE_REFERENCE_EQUATION.provenance,
    )


def patient_dead_space_excluding_apparatus_ml(
    vt_ml: float,
    model: PatientDeadSpaceModel,
    *,
    weight_kg: float | None = None,
    age_years: float | None = None,
) -> float:
    """Calculate patient physiologic VD excluding apparatus dead space.

    The returned value must not already contain any separately entered circuit,
    connector, sensor, filter, ETT, or other apparatus dead space. Numa total
    anatomic dead space and descriptive cohort profiles are deliberately not
    supported patient-VD modes.

    The composite reference requires explicit weight and age. There is no
    hidden fallback when those inputs are absent.
    """
    _require_positive("vt_ml", vt_ml)
    if isinstance(model, UserDefinedPatientVdVt):
        fraction = model.patient_vd_vt_excluding_apparatus
        return vt_ml * fraction
    if isinstance(model, PearsallBenchmarkPatientDeadSpace):
        return vt_ml * PEARSALL_VD_VT_BENCHMARK.value
    if isinstance(model, NumaFletcherCompositeReference):
        if weight_kg is None or age_years is None:
            raise InputValidationError(
                "NumaFletcherCompositeReference requires explicit "
                "weight_kg and age_years"
            )
        return numa_fletcher_composite_reference(
            weight_kg=weight_kg,
            age_years=age_years,
            vt_ml=vt_ml,
        ).patient_vd_ml_excluding_apparatus
    raise InputValidationError(
        "unsupported patient dead-space model; provide a patient-only "
        "physiologic VD/VT mode that excludes apparatus"
    )


def total_dead_space_ml(
    patient_vd_ml_excluding_apparatus: float,
    apparatus_vd_ml: float,
) -> float:
    """Sum patient-only physiologic VD and separately entered apparatus VD."""
    _require_nonnegative(
        "patient_vd_ml_excluding_apparatus",
        patient_vd_ml_excluding_apparatus,
    )
    _require_nonnegative("apparatus_vd_ml", apparatus_vd_ml)
    total = patient_vd_ml_excluding_apparatus + apparatus_vd_ml
    _require_nonnegative("total dead space", total)
    return total


def dead_space_fraction(vd_total_ml: float, vt_ml: float) -> float:
    """Return cumulative patient-plus-apparatus VD/VT."""
    _require_physical_dead_space(vt_ml, vd_total_ml)
    return vd_total_ml / vt_ml


def alveolar_tidal_volume_ml(vt_ml: float, vd_total_ml: float) -> float:
    _require_physical_dead_space(vt_ml, vd_total_ml)
    return vt_ml - vd_total_ml


def alveolar_minute_ventilation_ml_min(
    rr_bpm: float, alveolar_vt_ml_value: float
) -> float:
    _require_positive("rr_bpm", rr_bpm)
    _require_positive("alveolar_vt_ml", alveolar_vt_ml_value)
    result = rr_bpm * alveolar_vt_ml_value
    _require_positive("alveolar minute ventilation", result)
    return result


def relative_co2_burden(
    baseline_alveolar_ve_ml_min: float,
    current_alveolar_ve_ml_min: float,
) -> float:
    """Return VA_baseline / VA_current under the stable-VCO2 assumption."""
    _require_positive("baseline_alveolar_ve_ml_min", baseline_alveolar_ve_ml_min)
    _require_positive("current_alveolar_ve_ml_min", current_alveolar_ve_ml_min)
    return baseline_alveolar_ve_ml_min / current_alveolar_ve_ml_min


def baseline_calibrated_paco2_mechanistic_mmHg(
    paco2_baseline_mmHg: float,
    baseline_alveolar_ve_ml_min: float,
    current_alveolar_ve_ml_min: float,
) -> float:
    """Mechanistic baseline-calibrated estimate, not a patient prediction."""
    _require_positive("paco2_baseline_mmHg", paco2_baseline_mmHg)
    burden = relative_co2_burden(
        baseline_alveolar_ve_ml_min, current_alveolar_ve_ml_min
    )
    return paco2_baseline_mmHg * burden


def rr_required_to_preserve_alveolar_ventilation(
    baseline_alveolar_ve_ml_min: float,
    new_vt_ml: float,
    new_vd_ml: float,
) -> float:
    _require_positive("baseline_alveolar_ve_ml_min", baseline_alveolar_ve_ml_min)
    denominator = alveolar_tidal_volume_ml(new_vt_ml, new_vd_ml)
    return baseline_alveolar_ve_ml_min / denominator


def apparatus_dead_space_percent_vt(
    apparatus_vd_ml: float, vt_ml: float
) -> float:
    _require_nonnegative("apparatus_vd_ml", apparatus_vd_ml)
    _require_positive("vt_ml", vt_ml)
    return 100.0 * apparatus_vd_ml / vt_ml


def vt_to_apparatus_dead_space_ratio(
    vt_ml: float, apparatus_vd_ml: float
) -> float | None:
    """Return VT/apparatus-VD, or None when apparatus VD is zero."""
    _require_positive("vt_ml", vt_ml)
    _require_nonnegative("apparatus_vd_ml", apparatus_vd_ml)
    if apparatus_vd_ml == 0.0:
        return None
    return vt_ml / apparatus_vd_ml


def calculate_ventilation(
    inputs: VentilationInputs,
    patient_model: PatientDeadSpaceModel,
    apparatus_components: Iterable[ApparatusComponent],
) -> VentilationState:
    """Calculate a complete one-compartment ventilation state."""
    if isinstance(patient_model, PearsallBenchmarkPatientDeadSpace):
        _warn_pearsall_context(inputs.weight_kg, inputs.age_years)

    vt = calculate_tidal_volume_ml(
        inputs.weight_kg,
        vt_ml_kg=inputs.vt_ml_kg,
        vt_ml=inputs.vt_ml,
    )
    apparatus_vd = apparatus_stack_dead_space_ml(apparatus_components)

    composite: NumaFletcherCompositeComponents | None = None
    if isinstance(patient_model, NumaFletcherCompositeReference):
        composite = numa_fletcher_composite_reference(
            weight_kg=inputs.weight_kg,
            age_years=inputs.age_years,
            vt_ml=vt,
        )
        patient_vd = composite.patient_vd_ml_excluding_apparatus
    else:
        patient_vd = patient_dead_space_excluding_apparatus_ml(vt, patient_model)

    total_vd = total_dead_space_ml(patient_vd, apparatus_vd)
    total_fraction = dead_space_fraction(total_vd, vt)
    alveolar_vt = alveolar_tidal_volume_ml(vt, total_vd)
    alveolar_ve = alveolar_minute_ventilation_ml_min(inputs.rr_bpm, alveolar_vt)
    return VentilationState(
        vt_ml=vt,
        patient_vd_ml_excluding_apparatus=patient_vd,
        apparatus_vd_ml=apparatus_vd,
        total_vd_ml=total_vd,
        total_vd_vt=total_fraction,
        alveolar_vt_ml=alveolar_vt,
        alveolar_ve_ml_min=alveolar_ve,
        apparatus_dead_space_percent_vt=apparatus_dead_space_percent_vt(
            apparatus_vd, vt
        ),
        vt_to_apparatus_dead_space_ratio=vt_to_apparatus_dead_space_ratio(
            vt, apparatus_vd
        ),
        patient_airway_dead_space_ml=(
            None if composite is None else composite.airway_ds_ml
        ),
        patient_alveolar_tidal_volume_ml=(
            None if composite is None else composite.alveolar_tidal_volume_ml
        ),
        patient_alveolar_dead_space_ml=(
            None if composite is None else composite.alveolar_ds_ml
        ),
    )


def numa_total_anatomic_dead_space_reference(
    weight_kg: float, age_years: float
) -> NumaTotalAnatomicDeadSpaceReference:
    """Return Numa TOTAL ANATOMIC dead space as a reference-only object.

    The source reported extrathoracic measurements from 7 days to 14.2 years
    and intrathoracic measurements from 18 days to 14.7 years. Because the
    result is total anatomic dead space, the non-extrapolated common overlap is
    18 days to 14.2 years. The return type is not accepted as patient
    physiologic dead space.
    """
    _require_positive("weight_kg", weight_kg)
    _require_nonnegative("age_years", age_years)

    in_extrathoracic_range = (
        NUMA_EXTRATHORACIC_MIN_AGE_YEARS.value
        <= age_years
        <= NUMA_EXTRATHORACIC_MAX_AGE_YEARS.value
    )
    in_intrathoracic_range = (
        NUMA_INTRATHORACIC_MIN_AGE_YEARS.value
        <= age_years
        <= NUMA_INTRATHORACIC_MAX_AGE_YEARS.value
    )
    if not (in_extrathoracic_range and in_intrathoracic_range):
        warnings.warn(
            "Numa 1996 total-anatomic reference is outside the common audited "
            "source-age overlap: extrathoracic measurements covered 7 days–"
            "14.2 years and intrathoracic measurements covered 18 days–14.7 "
            "years; this warning does not validate extrapolation",
            SourceDomainWarning,
            stacklevel=2,
        )

    scale = NUMA_TOTAL_ANATOMIC_INTERCEPT.value - (
        NUMA_LOG_COEFFICIENT.value
        * math.log(NUMA_AGE_OFFSET_YEARS.value + age_years)
    )
    if scale <= 0.0:
        raise NonPhysicalStateError(
            "Numa equation produced non-positive total anatomic dead space; "
            "the requested age is outside a physically usable domain"
        )
    return NumaTotalAnatomicDeadSpaceReference(
        total_anatomic_dead_space_ml_kg=scale,
        total_anatomic_dead_space_ml=weight_kg * scale,
        provenance=NUMA_TOTAL_ANATOMIC_SCALING.provenance,
    )


def vco2_lindahl_bja_1989_ml_min(weight_kg: float) -> float:
    """Lindahl BJA 1989 model for anesthetized surgical children."""
    _require_positive("weight_kg", weight_kg)
    if not (
        LINDAHL_BJA_MIN_WEIGHT_KG.value
        <= weight_kg
        <= LINDAHL_BJA_MAX_WEIGHT_KG.value
    ):
        warnings.warn(
            "weight is outside the reported 3.6–25 kg source range for "
            "Lindahl BJA 1989; the warning does not validate extrapolation",
            SourceDomainWarning,
            stacklevel=2,
        )
    result = LINDAHL_BJA_SLOPE.value * weight_kg + LINDAHL_BJA_INTERCEPT.value
    _require_positive("calculated VCO2", result)
    return result


def vco2_lindahl_cja_1989_ml_min(weight_kg: float) -> float:
    """Lindahl CJA 1989 sensitivity model using numerical weight in kg."""
    _require_positive("weight_kg", weight_kg)
    if not (
        LINDAHL_CJA_MIN_WEIGHT_KG.value
        <= weight_kg
        <= LINDAHL_CJA_MAX_WEIGHT_KG.value
    ):
        warnings.warn(
            "weight is outside the reported 2.8–26.5 kg source range for "
            "Lindahl CJA 1989; the warning does not validate extrapolation",
            SourceDomainWarning,
            stacklevel=2,
        )
    x = math.log(weight_kg)
    result = LINDAHL_CJA_LINEAR.value * x + LINDAHL_CJA_QUADRATIC.value * x**2
    if not math.isfinite(result) or result <= 0.0:
        raise NonPhysicalStateError(
            "Lindahl CJA 1989 equation produced non-positive or non-finite VCO2"
        )
    return result


def vco2_pearsall_brody_benchmark_ml_min(
    weight_kg: float, age_years: float
) -> float:
    """Return the inherited Pearsall/Brody named-benchmark VCO2 assumption.

    This function remains available for benchmark reproduction only. It is not
    classified as a modern measured empirical default and is not connected to
    an absolute VCO2/VA PaCO2 output.
    """
    _require_positive("weight_kg", weight_kg)
    _require_nonnegative("age_years", age_years)
    _warn_pearsall_context(weight_kg, age_years)
    result = PEARSALL_BRODY_COEFFICIENT.value * weight_kg ** (
        PEARSALL_BRODY_EXPONENT.value
    )
    _require_positive("calculated VCO2", result)
    return result
