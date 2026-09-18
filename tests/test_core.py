import math
import warnings

import pytest

from paeddeadspace import (
    ApparatusComponent,
    NumaFletcherCompositeReference,
    InputValidationError,
    NonPhysicalStateError,
    ParameterClassification,
    PatientDeadSpaceModel,
    PearsallBenchmarkPatientDeadSpace,
    Provenance,
    SourceDomainWarning,
    UserDefinedPatientVdVt,
    VentilationInputs,
    WILLIAMS_TERM_INFANT_REFERENCE_PROFILE,
    WilliamsTermInfantReferenceProfile,
    alveolar_minute_ventilation_ml_min,
    baseline_calibrated_paco2_mechanistic_mmHg,
    calculate_tidal_volume_ml,
    calculate_ventilation,
    numa_fletcher_composite_reference,
    numa_total_anatomic_dead_space_reference,
    patient_dead_space_excluding_apparatus_ml,
    relative_co2_burden,
    rr_required_to_preserve_alveolar_ventilation,
    vco2_lindahl_bja_1989_ml_min,
    vco2_lindahl_cja_1989_ml_min,
    vco2_pearsall_brody_benchmark_ml_min,
)


USER_SOURCE = Provenance(
    classification=ParameterClassification.USER_DEFINED,
    source_id="TEST_USER_APPARATUS_INPUT",
    citation="Deterministic test fixture",
    context="User-entered apparatus volume used for arithmetic testing.",
)

WILLIAMS_SOURCE = Provenance(
    classification=ParameterClassification.MEASURED_EMPIRICAL,
    source_id="WILLIAMS_2022_STARTER_VOLUMES",
    citation="Williams et al., Pediatric Research, 2022",
    context="Starter apparatus/ETT volumes listed in the audited specification.",
    doi="10.1038/s41390-021-01388-8",
)


def component(name: str, volume: float, *, active: bool = True) -> ApparatusComponent:
    return ApparatusComponent(
        name=name,
        dead_space_ml=volume,
        active=active,
        provenance=USER_SOURCE,
        qualification="User-defined numeric dead-space entry for test",
    )


def state_for(weight: float, apparatus_ml: float, patient_vd_vt: float = 0.30):
    return calculate_ventilation(
        VentilationInputs(
            weight_kg=weight,
            age_years=2.0,
            rr_bpm=20.0,
            vt_ml_kg=8.0,
        ),
        UserDefinedPatientVdVt(patient_vd_vt),
        (component("apparatus", apparatus_ml),),
    )


def test_hand_computable_core_arithmetic_and_active_stack_only():
    state = calculate_ventilation(
        VentilationInputs(
            weight_kg=10.0,
            age_years=5.0,
            rr_bpm=20.0,
            vt_ml_kg=8.0,
        ),
        UserDefinedPatientVdVt(
            patient_vd_vt_excluding_apparatus=0.25
        ),
        (
            component("active A", 5.0),
            component("inactive B", 100.0, active=False),
            component("active C", 3.0),
        ),
    )

    assert state.vt_ml == pytest.approx(80.0)
    assert state.patient_vd_ml_excluding_apparatus == pytest.approx(20.0)
    assert state.apparatus_vd_ml == pytest.approx(8.0)
    assert state.total_vd_ml == pytest.approx(28.0)
    assert state.total_vd_vt == pytest.approx(0.35)
    assert state.alveolar_vt_ml == pytest.approx(52.0)
    assert state.alveolar_ve_ml_min == pytest.approx(1040.0)
    assert state.apparatus_dead_space_percent_vt == pytest.approx(10.0)
    assert state.vt_to_apparatus_dead_space_ratio == pytest.approx(10.0)


def test_user_defined_vd_vt_name_and_interpretation_exclude_apparatus():
    model = UserDefinedPatientVdVt(
        patient_vd_vt_excluding_apparatus=0.30
    )
    assert model.patient_vd_vt_excluding_apparatus == pytest.approx(0.30)
    assert "apparatus explicitly excluded" in model.interpretation

    with pytest.raises(TypeError):
        UserDefinedPatientVdVt(vd_vt=0.30)  # type: ignore[call-arg]


def test_absolute_and_weight_normalized_tidal_volume_are_mutually_exclusive():
    assert calculate_tidal_volume_ml(5.0, vt_ml_kg=6.0) == pytest.approx(30.0)
    assert calculate_tidal_volume_ml(5.0, vt_ml=31.0) == pytest.approx(31.0)
    with pytest.raises(InputValidationError, match="exactly one"):
        calculate_tidal_volume_ml(5.0)
    with pytest.raises(InputValidationError, match="exactly one"):
        calculate_tidal_volume_ml(5.0, vt_ml_kg=6.0, vt_ml=30.0)


def test_nonphysical_vd_equal_to_or_greater_than_vt_fails_clearly():
    inputs = VentilationInputs(
        weight_kg=2.0,
        age_years=0.1,
        rr_bpm=30.0,
        vt_ml_kg=8.0,
    )
    with pytest.raises(NonPhysicalStateError, match="model breakdown"):
        calculate_ventilation(
            inputs,
            UserDefinedPatientVdVt(0.75),
            (component("large component", 4.0),),
        )

    with pytest.raises(NonPhysicalStateError, match="model breakdown"):
        rr_required_to_preserve_alveolar_ventilation(500.0, 20.0, 20.0)


def test_relative_co2_and_baseline_calibrated_paco2_are_hand_computable():
    assert relative_co2_burden(1000.0, 800.0) == pytest.approx(1.25)
    assert baseline_calibrated_paco2_mechanistic_mmHg(
        40.0, 1000.0, 800.0
    ) == pytest.approx(50.0)


def test_pearsall_published_sample_requires_about_43_breaths_per_minute():
    inputs = VentilationInputs(
        weight_kg=10.0,
        age_years=2.0,
        rr_bpm=20.0,
        vt_ml_kg=8.0,
    )
    model = PearsallBenchmarkPatientDeadSpace()
    baseline = calculate_ventilation(inputs, model, ())
    with_apparatus = calculate_ventilation(
        inputs, model, (component("apparatus", 30.0),)
    )

    assert baseline.vt_ml == pytest.approx(80.0)
    assert baseline.patient_vd_ml_excluding_apparatus == pytest.approx(24.0)
    assert baseline.alveolar_ve_ml_min == pytest.approx(1120.0)
    assert with_apparatus.apparatus_vd_ml == pytest.approx(30.0)
    assert with_apparatus.total_vd_ml == pytest.approx(54.0)
    assert with_apparatus.alveolar_vt_ml == pytest.approx(26.0)

    required_rr = rr_required_to_preserve_alveolar_ventilation(
        baseline.alveolar_ve_ml_min,
        with_apparatus.vt_ml,
        with_apparatus.total_vd_ml,
    )
    assert required_rr == pytest.approx(1120.0 / 26.0)
    assert required_rr == pytest.approx(43.0, abs=0.1)


def test_pearsall_benchmark_8_to_55_ml_direction_and_hand_magnitude():
    inputs = VentilationInputs(
        weight_kg=10.0,
        age_years=2.0,
        rr_bpm=20.0,
        vt_ml_kg=8.0,
    )
    model = PearsallBenchmarkPatientDeadSpace()
    low = calculate_ventilation(inputs, model, (component("DS", 8.0),))
    high = calculate_ventilation(inputs, model, (component("DS", 55.0),))

    assert low.alveolar_ve_ml_min == pytest.approx(960.0)
    assert high.alveolar_ve_ml_min == pytest.approx(20.0)
    assert relative_co2_burden(
        low.alveolar_ve_ml_min, high.alveolar_ve_ml_min
    ) == pytest.approx(48.0)
    assert vco2_pearsall_brody_benchmark_ml_min(10.0, 2.0) == pytest.approx(
        5.56 * 10.0**1.05
    )


def test_added_apparatus_requires_higher_rr_to_preserve_baseline_va():
    baseline = state_for(weight=10.0, apparatus_ml=0.0)
    with_apparatus = state_for(weight=10.0, apparatus_ml=22.0)
    required_rr = rr_required_to_preserve_alveolar_ventilation(
        baseline.alveolar_ve_ml_min,
        with_apparatus.vt_ml,
        with_apparatus.total_vd_ml,
    )
    assert required_rr == pytest.approx((20.0 * 56.0) / 34.0)
    assert required_rr > 20.0


def test_same_apparatus_volume_has_greater_relative_burden_at_lower_weight():
    low_baseline = state_for(weight=5.0, apparatus_ml=0.0)
    low_added = state_for(weight=5.0, apparatus_ml=22.0)
    high_baseline = state_for(weight=10.0, apparatus_ml=0.0)
    high_added = state_for(weight=10.0, apparatus_ml=22.0)

    low_burden = relative_co2_burden(
        low_baseline.alveolar_ve_ml_min, low_added.alveolar_ve_ml_min
    )
    high_burden = relative_co2_burden(
        high_baseline.alveolar_ve_ml_min, high_added.alveolar_ve_ml_min
    )
    assert low_burden == pytest.approx(28.0 / 6.0)
    assert high_burden == pytest.approx(56.0 / 34.0)
    assert low_burden > high_burden > 1.0


def test_four_ml_apparatus_sensitivity_is_greater_at_two_kg_than_three_kg():
    two_base = state_for(weight=2.0, apparatus_ml=0.0)
    two_added = state_for(weight=2.0, apparatus_ml=4.0)
    three_base = state_for(weight=3.0, apparatus_ml=0.0)
    three_added = state_for(weight=3.0, apparatus_ml=4.0)

    burden_two = relative_co2_burden(
        two_base.alveolar_ve_ml_min, two_added.alveolar_ve_ml_min
    )
    burden_three = relative_co2_burden(
        three_base.alveolar_ve_ml_min, three_added.alveolar_ve_ml_min
    )
    assert burden_two == pytest.approx(11.2 / 7.2)
    assert burden_three == pytest.approx(16.8 / 12.8)
    assert burden_two > burden_three > 1.0


@pytest.mark.parametrize(
    ("name", "volume"),
    (
        ("Capnostat-5", 0.8),
        ("ETT 2.0 mm", 1.2),
        ("ETT 2.5 mm", 1.8),
        ("ETT 3.0 mm", 2.0),
        ("ETT 3.5 mm", 3.0),
        ("ETT 4.0 mm", 3.2),
    ),
)
def test_sourced_starter_volumes_remain_explicit_apparatus_inputs(name, volume):
    item = ApparatusComponent(
        name=name,
        dead_space_ml=volume,
        active=True,
        provenance=WILLIAMS_SOURCE,
        qualification="Published starter volume; functional equivalence not assumed",
    )
    state = calculate_ventilation(
        VentilationInputs(
            weight_kg=5.0,
            age_years=1.0,
            rr_bpm=20.0,
            vt_ml_kg=8.0,
        ),
        UserDefinedPatientVdVt(0.30),
        (item,),
    )
    assert state.apparatus_vd_ml == pytest.approx(volume)


def test_named_vco2_equations_match_hand_computable_values():
    assert vco2_lindahl_bja_1989_ml_min(10.0) == pytest.approx(54.4)

    weight = math.exp(2.0)
    assert vco2_lindahl_cja_1989_ml_min(weight) == pytest.approx(49.5)


@pytest.mark.parametrize("weight", [3.0, 26.0])
def test_lindahl_bja_warns_outside_3_6_to_25_kg(weight):
    with pytest.warns(SourceDomainWarning, match="3.6–25"):
        vco2_lindahl_bja_1989_ml_min(weight)


def test_lindahl_cja_and_pearsall_source_domain_warnings():
    with pytest.warns(SourceDomainWarning, match="2.8–26.5"):
        vco2_lindahl_cja_1989_ml_min(2.0)
    with pytest.warns(SourceDomainWarning, match="Pearsall"):
        vco2_pearsall_brody_benchmark_ml_min(20.0, 4.0)

    with pytest.warns(SourceDomainWarning, match="Pearsall"):
        calculate_ventilation(
            VentilationInputs(
                weight_kg=20.0,
                age_years=4.0,
                rr_bpm=20.0,
                vt_ml_kg=8.0,
            ),
            PearsallBenchmarkPatientDeadSpace(),
            (),
        )


def test_numa_is_reference_only_and_matches_specified_equation():
    result = numa_total_anatomic_dead_space_reference(10.0, 3.0)
    expected_ml_kg = 3.28 - 0.56 * math.log(4.0)
    assert result.total_anatomic_dead_space_ml_kg == pytest.approx(expected_ml_kg)
    assert result.total_anatomic_dead_space_ml == pytest.approx(10.0 * expected_ml_kg)
    assert "not physiologic-VD default" in result.interpretation

    with pytest.raises(InputValidationError, match="unsupported"):
        calculate_ventilation(
            VentilationInputs(
                weight_kg=10.0,
                age_years=3.0,
                rr_bpm=20.0,
                vt_ml_kg=8.0,
            ),
            result,  # type: ignore[arg-type]
            (),
        )


@pytest.mark.parametrize("age_years", [10.0 / 365.25, 15.0])
def test_numa_warns_outside_common_audited_source_age_overlap(age_years):
    with pytest.warns(SourceDomainWarning, match="extrathoracic"):
        result = numa_total_anatomic_dead_space_reference(10.0, age_years)
    assert result.total_anatomic_dead_space_ml > 0.0


def test_alveolar_minute_ventilation_rejects_zero_alveolar_tidal_volume():
    with pytest.raises(InputValidationError):
        alveolar_minute_ventilation_ml_min(20.0, 0.0)


@pytest.mark.parametrize(
    ("vt_ml", "expected_fraction"),
    (
        (40.0, 0.33175),
        (50.0, 0.2854),
        (60.0, 0.2545),
        (80.0, 0.215875),
    ),
)
def test_composite_reference_arithmetic(vt_ml, expected_fraction):
    result = numa_fletcher_composite_reference(
        weight_kg=10.0,
        age_years=5.0,
        vt_ml=vt_ml,
    )
    assert result.patient_vd_vt_excluding_apparatus == pytest.approx(
        expected_fraction
    )


def test_composite_components_and_apparatus_remain_separate():
    result = numa_fletcher_composite_reference(10.0, 5.0, 80.0)
    assert result.airway_ds_ml == pytest.approx(10.3)
    assert result.alveolar_tidal_volume_ml == pytest.approx(69.7)
    assert result.alveolar_ds_ml == pytest.approx(6.97)
    assert result.patient_vd_ml_excluding_apparatus == pytest.approx(17.27)

    state = calculate_ventilation(
        VentilationInputs(
            weight_kg=10.0,
            age_years=5.0,
            rr_bpm=20.0,
            vt_ml=80.0,
        ),
        NumaFletcherCompositeReference(),
        (component("separate apparatus", 8.0),),
    )
    assert state.patient_vd_ml_excluding_apparatus == pytest.approx(17.27)
    assert state.apparatus_vd_ml == pytest.approx(8.0)
    assert state.total_vd_ml == pytest.approx(25.27)
    assert state.patient_airway_dead_space_ml == pytest.approx(10.3)
    assert state.patient_alveolar_tidal_volume_ml == pytest.approx(69.7)
    assert state.patient_alveolar_dead_space_ml == pytest.approx(6.97)


def test_composite_rejects_vt_at_or_below_airway_component():
    with pytest.raises(NonPhysicalStateError, match="must be greater"):
        numa_fletcher_composite_reference(10.0, 5.0, 10.3)
    with pytest.raises(NonPhysicalStateError, match="nonphysical"):
        numa_fletcher_composite_reference(10.0, 5.0, 10.0)


def test_composite_direct_patient_function_requires_weight_and_age():
    with pytest.raises(InputValidationError, match="weight_kg and age_years"):
        patient_dead_space_excluding_apparatus_ml(
            80.0, NumaFletcherCompositeReference()
        )


def test_composite_numa_component_source_domain_warning():
    with pytest.warns(
        SourceDomainWarning, match="extrapolation is not validation"
    ):
        numa_fletcher_composite_reference(10.0, 0.0, 80.0)
    with pytest.warns(
        SourceDomainWarning, match="extrapolation is not validation"
    ):
        numa_fletcher_composite_reference(10.0, 15.0, 80.0)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        numa_fletcher_composite_reference(10.0, 5.0, 80.0)
    assert not [item for item in caught if item.category is SourceDomainWarning]


def test_williams_profile_retains_exact_term_control_values():
    profile = WILLIAMS_TERM_INFANT_REFERENCE_PROFILE
    expected = (
        (profile.physiologic_dead_space_ml_kg, 3.5, (2.8, 4.3)),
        (profile.total_anatomical_dead_space_ml_kg, 2.7, (2.4, 3.2)),
        (profile.apparatus_dead_space_ml_kg, 1.2, (1.1, 1.4)),
        (
            profile.anatomical_minus_apparatus_dead_space_ml_kg,
            1.6,
            (1.1, 2.2),
        ),
        (profile.alveolar_dead_space_ml_kg, 0.5, (0.3, 1.2)),
        (profile.tidal_volume_ml_kg, 6.4, (5.4, 7.6)),
        (profile.dead_space_tidal_volume_ratio, 0.52, (0.43, 0.62)),
        (profile.alveolar_ventilation_ml_kg_min, 111.0, (81.0, 159.0)),
    )
    for interval, median, iqr in expected:
        assert interval.median == pytest.approx(median)
        assert interval.iqr == pytest.approx(iqr)


def test_williams_profile_is_reference_only_not_patient_model():
    profile = WilliamsTermInfantReferenceProfile()
    assert not isinstance(profile, PatientDeadSpaceModel)
    assert "reference-only" in profile.interpretation
    assert not hasattr(profile, "patient_vd_vt_excluding_apparatus")

    with pytest.raises(InputValidationError, match="unsupported"):
        calculate_ventilation(
            VentilationInputs(
                weight_kg=3.5,
                age_years=0.05,
                rr_bpm=30.0,
                vt_ml_kg=6.0,
            ),
            profile,  # type: ignore[arg-type]
            (),
        )
