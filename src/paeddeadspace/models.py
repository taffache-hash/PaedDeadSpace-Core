"""Typed immutable data models for PaedDeadSpace v1.0.0."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .provenance import (
    HEALTHY_INTUBATED_COMPOSITE_REFERENCE_EQUATION,
    WILLIAMS_TERM_CONTROL_2022,
    Provenance,
)

USER_DEFINED = {"classification": "user-defined"}
DERIVED = {"classification": "derived"}
PROVENANCE_CLASSIFIED = {"classification": "provided-by-provenance"}
ASSUMPTION_BOUND = {"classification": "assumption-bound interpretation"}
REFERENCE_ONLY = {"classification": "reference-only descriptive data"}


class PaedDeadSpaceError(ValueError):
    """Base exception for invalid scientific-core operations."""


class InputValidationError(PaedDeadSpaceError):
    """Raised for invalid, missing, or ambiguous inputs."""


class NonPhysicalStateError(PaedDeadSpaceError):
    """Raised when the one-compartment calculation enters model breakdown."""


class SourceDomainWarning(UserWarning):
    """Warns that a source equation is being used outside its audited context."""


class PatientDeadSpaceModel:
    """Nominal interface for accepted patient-only dead-space modes.

    Reference-only descriptive objects deliberately do not inherit from this
    interface and are rejected by the computational core.
    """

    __slots__ = ()


def _finite(name: str, value: float) -> None:
    if not math.isfinite(value):
        raise InputValidationError(f"{name} must be finite")


def _positive(name: str, value: float) -> None:
    _finite(name, value)
    if value <= 0.0:
        raise InputValidationError(f"{name} must be > 0")


def _nonnegative(name: str, value: float) -> None:
    _finite(name, value)
    if value < 0.0:
        raise InputValidationError(f"{name} must be >= 0")


@dataclass(frozen=True, slots=True)
class ApparatusComponent:
    """A user-supplied apparatus component with mandatory provenance.

    ``qualification`` should state whether the entry is measured functional
    dead space, manufacturer internal/geometric volume, or another estimate.
    The core does not silently convert geometric volume to functional dead
    space.
    """

    name: str = field(metadata=USER_DEFINED)
    dead_space_ml: float = field(metadata=PROVENANCE_CLASSIFIED)
    active: bool = field(metadata=USER_DEFINED)
    provenance: Provenance = field(metadata=PROVENANCE_CLASSIFIED)
    qualification: str = field(metadata=USER_DEFINED)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise InputValidationError("apparatus component name must not be empty")
        _nonnegative("apparatus component dead_space_ml", self.dead_space_ml)
        if not self.qualification.strip():
            raise InputValidationError(
                "apparatus component qualification must not be empty"
            )


@dataclass(frozen=True, slots=True)
class UserDefinedPatientVdVt(PatientDeadSpaceModel):
    """User-defined PATIENT physiologic VD/VT excluding apparatus.

    ``patient_vd_vt_excluding_apparatus`` must not contain dead space from any
    separately entered ETT, connector, sensor, filter, circuit component, or
    other apparatus. A measured clinical VD/VT that includes apparatus cannot
    be used here without scientifically justified decomposition.
    """

    patient_vd_vt_excluding_apparatus: float = field(metadata=USER_DEFINED)
    interpretation: str = field(
        default="patient-physiologic-VD/VT-only; apparatus explicitly excluded",
        init=False,
        metadata=ASSUMPTION_BOUND,
    )

    def __post_init__(self) -> None:
        _finite(
            "patient_vd_vt_excluding_apparatus",
            self.patient_vd_vt_excluding_apparatus,
        )
        if not 0.0 <= self.patient_vd_vt_excluding_apparatus <= 1.0:
            raise InputValidationError(
                "patient_vd_vt_excluding_apparatus must be between 0 and 1 "
                "inclusive"
            )


@dataclass(frozen=True, slots=True)
class PearsallBenchmarkPatientDeadSpace(PatientDeadSpaceModel):
    """Named Pearsall benchmark assumption: patient-only VD/VT = 0.30.

    The value excludes separately entered apparatus dead space. This class has
    no configurable value so the inherited benchmark cannot be mistaken for a
    universal physiologic default.
    """

    interpretation: str = field(
        default=(
            "named-benchmark patient physiologic VD/VT; apparatus explicitly "
            "excluded"
        ),
        init=False,
        metadata=ASSUMPTION_BOUND,
    )


@dataclass(frozen=True, slots=True)
class NumaFletcherCompositeReference(PatientDeadSpaceModel):
    """Select the Numa/Fletcher composite patient-only reference mode.

    This is an evidence-informed sensitivity/reference construction, not a
    clinical default. Reference status does not imply a healthy source
    population: the Fletcher component came from children undergoing thoracic
    surgery, with the 0.10 mean applying to those with normal pulmonary
    circulation. Its empirical components came from separate studies; the
    combined equation was not directly published or validated in either one.
    Apparatus dead space remains separate.
    """

    provenance: Provenance = field(
        default=HEALTHY_INTUBATED_COMPOSITE_REFERENCE_EQUATION.provenance,
        init=False,
        metadata=PROVENANCE_CLASSIFIED,
    )
    interpretation: str = field(
        default=(
            "assumption/model-construction reference; patient-only VD with "
            "apparatus explicitly excluded"
        ),
        init=False,
        metadata=ASSUMPTION_BOUND,
    )


@dataclass(frozen=True, slots=True)
class NumaFletcherCompositeComponents:
    """Transparent derived outputs from the Numa/Fletcher construction."""

    airway_ds_ml: float = field(metadata=DERIVED)
    alveolar_tidal_volume_ml: float = field(metadata=DERIVED)
    alveolar_ds_ml: float = field(metadata=DERIVED)
    patient_vd_ml_excluding_apparatus: float = field(metadata=DERIVED)
    patient_vd_vt_excluding_apparatus: float = field(metadata=DERIVED)
    provenance: Provenance = field(metadata=PROVENANCE_CLASSIFIED)
    interpretation: str = field(
        default=(
            "derived/model output from separate empirical components; "
            "apparatus dead space excluded"
        ),
        init=False,
        metadata=ASSUMPTION_BOUND,
    )

    @property
    def intrathoracic_airway_ds_ml(self) -> float:
        return self.airway_ds_ml

    @property
    def patient_vd_ml(self) -> float:
        return self.patient_vd_ml_excluding_apparatus

    @property
    def patient_vd_vt(self) -> float:
        return self.patient_vd_vt_excluding_apparatus


@dataclass(frozen=True, slots=True)
class VentilationInputs:
    """Explicit inputs; exactly one tidal-volume entry method is required."""

    weight_kg: float = field(metadata=USER_DEFINED)
    age_years: float = field(metadata=USER_DEFINED)
    rr_bpm: float = field(metadata=USER_DEFINED)
    vt_ml_kg: float | None = field(default=None, metadata=USER_DEFINED)
    vt_ml: float | None = field(default=None, metadata=USER_DEFINED)
    paco2_baseline_mmHg: float | None = field(default=None, metadata=USER_DEFINED)
    paco2_target_mmHg: float | None = field(default=None, metadata=USER_DEFINED)

    def __post_init__(self) -> None:
        _positive("weight_kg", self.weight_kg)
        _nonnegative("age_years", self.age_years)
        _positive("rr_bpm", self.rr_bpm)
        if (self.vt_ml_kg is None) == (self.vt_ml is None):
            raise InputValidationError("provide exactly one of vt_ml_kg or vt_ml")
        if self.vt_ml_kg is not None:
            _positive("vt_ml_kg", self.vt_ml_kg)
        if self.vt_ml is not None:
            _positive("vt_ml", self.vt_ml)
        if self.paco2_baseline_mmHg is not None:
            _positive("paco2_baseline_mmHg", self.paco2_baseline_mmHg)
        if self.paco2_target_mmHg is not None:
            _positive("paco2_target_mmHg", self.paco2_target_mmHg)


@dataclass(frozen=True, slots=True)
class VentilationState:
    """Derived one-compartment outputs for a physical state where total VD < VT."""

    vt_ml: float = field(metadata=DERIVED)
    patient_vd_ml_excluding_apparatus: float = field(metadata=DERIVED)
    apparatus_vd_ml: float = field(metadata=DERIVED)
    total_vd_ml: float = field(metadata=DERIVED)
    total_vd_vt: float = field(metadata=DERIVED)
    alveolar_vt_ml: float = field(metadata=DERIVED)
    alveolar_ve_ml_min: float = field(metadata=DERIVED)
    apparatus_dead_space_percent_vt: float = field(metadata=DERIVED)
    vt_to_apparatus_dead_space_ratio: float | None = field(metadata=DERIVED)
    patient_airway_dead_space_ml: float | None = field(
        default=None, metadata=DERIVED
    )
    patient_alveolar_tidal_volume_ml: float | None = field(
        default=None, metadata=DERIVED
    )
    patient_alveolar_dead_space_ml: float | None = field(
        default=None, metadata=DERIVED
    )


@dataclass(frozen=True, slots=True)
class NumaTotalAnatomicDeadSpaceReference:
    """Reference result that is explicitly not a physiologic-VD model input."""

    total_anatomic_dead_space_ml_kg: float = field(metadata=DERIVED)
    total_anatomic_dead_space_ml: float = field(metadata=DERIVED)
    provenance: Provenance = field(metadata=PROVENANCE_CLASSIFIED)
    interpretation: str = field(
        default="total-anatomic-reference-only; not physiologic-VD default",
        init=False,
        metadata=ASSUMPTION_BOUND,
    )


@dataclass(frozen=True, slots=True)
class CohortReferenceInterval:
    """A descriptive cohort median and IQR, not an individual-patient value."""

    median: float = field(metadata=REFERENCE_ONLY)
    iqr: tuple[float, float] = field(metadata=REFERENCE_ONLY)
    unit: str = field(metadata=REFERENCE_ONLY)

    def __post_init__(self) -> None:
        _finite("reference median", self.median)
        _finite("reference IQR lower bound", self.iqr[0])
        _finite("reference IQR upper bound", self.iqr[1])
        if self.iqr[0] > self.median or self.median > self.iqr[1]:
            raise InputValidationError(
                "reference median must lie within the supplied IQR"
            )
        if not self.unit.strip():
            raise InputValidationError("reference interval unit must not be empty")


@dataclass(frozen=True, slots=True)
class WilliamsTermInfantReferenceProfile:
    """Williams term-control Table 2 descriptive cohort references.

    This object is intentionally non-computational and does not implement
    ``PatientDeadSpaceModel``. Group medians and IQRs are not algebraically
    decomposable into a single individual patient-only dead-space value.
    """

    physiologic_dead_space_ml_kg: CohortReferenceInterval = field(
        default=CohortReferenceInterval(3.5, (2.8, 4.3), "mL/kg"),
        init=False,
        metadata=REFERENCE_ONLY,
    )
    total_anatomical_dead_space_ml_kg: CohortReferenceInterval = field(
        default=CohortReferenceInterval(2.7, (2.4, 3.2), "mL/kg"),
        init=False,
        metadata=REFERENCE_ONLY,
    )
    apparatus_dead_space_ml_kg: CohortReferenceInterval = field(
        default=CohortReferenceInterval(1.2, (1.1, 1.4), "mL/kg"),
        init=False,
        metadata=REFERENCE_ONLY,
    )
    anatomical_minus_apparatus_dead_space_ml_kg: CohortReferenceInterval = field(
        default=CohortReferenceInterval(1.6, (1.1, 2.2), "mL/kg"),
        init=False,
        metadata=REFERENCE_ONLY,
    )
    alveolar_dead_space_ml_kg: CohortReferenceInterval = field(
        default=CohortReferenceInterval(0.5, (0.3, 1.2), "mL/kg"),
        init=False,
        metadata=REFERENCE_ONLY,
    )
    tidal_volume_ml_kg: CohortReferenceInterval = field(
        default=CohortReferenceInterval(6.4, (5.4, 7.6), "mL/kg"),
        init=False,
        metadata=REFERENCE_ONLY,
    )
    dead_space_tidal_volume_ratio: CohortReferenceInterval = field(
        default=CohortReferenceInterval(0.52, (0.43, 0.62), "dimensionless"),
        init=False,
        metadata=REFERENCE_ONLY,
    )
    alveolar_ventilation_ml_kg_min: CohortReferenceInterval = field(
        default=CohortReferenceInterval(111.0, (81.0, 159.0), "mL/kg/min"),
        init=False,
        metadata=REFERENCE_ONLY,
    )
    provenance: Provenance = field(
        default=WILLIAMS_TERM_CONTROL_2022,
        init=False,
        metadata=PROVENANCE_CLASSIFIED,
    )
    interpretation: str = field(
        default=(
            "reference-only term-control cohort medians/IQRs; not a "
            "patient dead-space computational mode or individual default"
        ),
        init=False,
        metadata=ASSUMPTION_BOUND,
    )


WILLIAMS_TERM_INFANT_REFERENCE_PROFILE = WilliamsTermInfantReferenceProfile()
