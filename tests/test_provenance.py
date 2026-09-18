from dataclasses import fields

import pytest

from paeddeadspace.models import (
    ApparatusComponent,
    NumaFletcherCompositeComponents,
    NumaFletcherCompositeReference,
    UserDefinedPatientVdVt,
    VentilationInputs,
    VentilationState,
    WilliamsTermInfantReferenceProfile,
)
from paeddeadspace.provenance import (
    BENCHMARK_EQUATIONS,
    EMPIRICAL_EQUATIONS,
    FLETCHER_1986,
    FLETCHER_ALVEOLAR_DEAD_SPACE_FRACTION,
    HEALTHY_INTUBATED_COMPOSITE_REFERENCE_EQUATION,
    MODEL_CONSTRUCTION_EQUATIONS,
    NUMA_INTRATHORACIC_1996,
    NUMA_INTRATHORACIC_DEAD_SPACE_ML_KG,
    PEARSALL_2014,
    PEARSALL_VD_VT_BENCHMARK,
    SCIENTIFIC_EQUATIONS,
    VT_PRESETS_ML_KG,
    WILLIAMS_TERM_CONTROL_2022,
    ParameterClassification,
    Provenance,
)


def test_measured_empirical_equations_and_constants_have_provenance():
    assert EMPIRICAL_EQUATIONS
    for equation in EMPIRICAL_EQUATIONS:
        assert equation.equation_id
        assert equation.formula
        assert equation.provenance.source_id
        assert equation.provenance.citation
        assert equation.provenance.context
        assert equation.provenance.classification is (
            ParameterClassification.MEASURED_EMPIRICAL
        )
        assert equation.constants
        for constant in equation.constants:
            assert constant.name
            assert constant.unit
            assert constant.provenance == equation.provenance


def test_pearsall_brody_equation_is_an_inherited_assumption_benchmark():
    assert len(BENCHMARK_EQUATIONS) == 1
    equation = BENCHMARK_EQUATIONS[0]
    assert equation.provenance is PEARSALL_2014
    assert equation.provenance.classification is ParameterClassification.ASSUMPTION
    assert "inherited" in equation.provenance.context
    assert "not a modern measured empirical default" in equation.provenance.context
    assert "0–36 months" in equation.provenance.context
    assert "2–17 kg" in equation.provenance.context
    assert "VT 8 mL/kg" in equation.provenance.context
    assert "VD/VT 0.30" in equation.provenance.context
    assert "RR 20/min" in equation.provenance.context
    assert equation not in EMPIRICAL_EQUATIONS
    assert equation in SCIENTIFIC_EQUATIONS
    assert all(
        constant.provenance.classification is ParameterClassification.ASSUMPTION
        for constant in equation.constants
    )


def test_pearsall_patient_vd_vt_is_an_assumption_not_a_default():
    assert PEARSALL_VD_VT_BENCHMARK.value == pytest.approx(0.30)
    assert PEARSALL_VD_VT_BENCHMARK.provenance.classification is (
        ParameterClassification.ASSUMPTION
    )
    assert "excluding separately entered apparatus" in (
        PEARSALL_VD_VT_BENCHMARK.provenance.context
    )
    assert "not a universal" in PEARSALL_VD_VT_BENCHMARK.provenance.context


def test_vt_presets_are_user_selected_with_explicit_evidence_context():
    assert [item.value for item in VT_PRESETS_ML_KG] == [4.0, 5.0, 6.0, 8.0, 10.0]
    assert all(
        item.provenance.classification is ParameterClassification.USER_DEFINED
        for item in VT_PRESETS_ML_KG
    )
    for item in VT_PRESETS_ML_KG:
        context = item.provenance.context.lower()
        assert "clinical default" in context
        assert "recommendation" in context

    for item in VT_PRESETS_ML_KG:
        evidence = {source.source_id: source for source in item.provenance.evidence_sources}
        assert evidence["SPAETH_2022_VT_CONTEXT"].doi == "10.1111/pan.14366"
        assert evidence["FELDMAN_2015_VT_CONTEXT"].doi == (
            "10.1213/ANE.0000000000000472"
        )

    assert "low-VT sensitivity/stress-test" in VT_PRESETS_ML_KG[0].provenance.context
    assert "age-appropriate neonatal use" in VT_PRESETS_ML_KG[0].provenance.context
    assert "historical comparator" in VT_PRESETS_ML_KG[-1].provenance.context


def test_source_context_boundaries_are_structurally_attached_to_equations():
    by_id = {equation.equation_id: equation for equation in SCIENTIFIC_EQUATIONS}

    numa = by_id["numa_1996_total_anatomic_dead_space"]
    numa_names = {constant.name for constant in numa.constants}
    assert "numa_extrathoracic_source_min_age" in numa_names
    assert "numa_extrathoracic_source_max_age" in numa_names
    assert "numa_intrathoracic_source_min_age" in numa_names
    assert "numa_intrathoracic_source_max_age" in numa_names

    bja = by_id["lindahl_bja_1989_vco2"]
    bja_values = {constant.name: constant.value for constant in bja.constants}
    assert bja_values["lindahl_bja_source_min_weight"] == pytest.approx(3.6)
    assert bja_values["lindahl_bja_source_max_weight"] == pytest.approx(25.0)


def test_input_and_output_model_fields_have_classification_metadata():
    for model in (
        ApparatusComponent,
        UserDefinedPatientVdVt,
        NumaFletcherCompositeReference,
        NumaFletcherCompositeComponents,
        VentilationInputs,
        VentilationState,
        WilliamsTermInfantReferenceProfile,
    ):
        for model_field in fields(model):
            assert "classification" in model_field.metadata


def test_provenance_rejects_missing_source_identifier():
    with pytest.raises(ValueError, match="source_id"):
        Provenance(
            classification=ParameterClassification.USER_DEFINED,
            source_id="",
            citation="User input",
            context="Test",
        )


def test_lindahl_bja_context_records_mixed_ventilation_source():
    from paeddeadspace.provenance import LINDAHL_BJA_1989

    context = LINDAHL_BJA_1989.context.lower()
    assert "38" in context
    assert "34" in context
    assert "controlled mechanical ventilation" in context
    assert "spontaneously" in context
    assert "3.6–25 kg" in LINDAHL_BJA_1989.context


def test_composite_component_constants_retain_empirical_provenance():
    assert NUMA_INTRATHORACIC_DEAD_SPACE_ML_KG.value == pytest.approx(1.03)
    assert NUMA_INTRATHORACIC_DEAD_SPACE_ML_KG.provenance is (
        NUMA_INTRATHORACIC_1996
    )
    assert NUMA_INTRATHORACIC_1996.classification is (
        ParameterClassification.MEASURED_EMPIRICAL
    )
    assert NUMA_INTRATHORACIC_1996.doi == "10.1152/jappl.1996.80.5.1485"

    assert FLETCHER_ALVEOLAR_DEAD_SPACE_FRACTION.value == pytest.approx(0.10)
    assert FLETCHER_ALVEOLAR_DEAD_SPACE_FRACTION.provenance is FLETCHER_1986
    assert FLETCHER_1986.classification is (
        ParameterClassification.MEASURED_EMPIRICAL
    )
    assert FLETCHER_1986.doi == "10.1213/00000539-198606000-00014"
    assert "not a universal" in FLETCHER_1986.context


def test_combined_composite_is_assumption_with_both_sources_linked():
    equation = HEALTHY_INTUBATED_COMPOSITE_REFERENCE_EQUATION
    assert MODEL_CONSTRUCTION_EQUATIONS == (equation,)
    assert equation in SCIENTIFIC_EQUATIONS
    assert equation not in EMPIRICAL_EQUATIONS
    assert equation.provenance.classification is ParameterClassification.ASSUMPTION
    assert "model construction" in equation.provenance.context.lower()
    assert "not directly published or validated" in equation.provenance.context

    evidence = {
        source.source_id: source for source in equation.provenance.evidence_sources
    }
    assert NUMA_INTRATHORACIC_1996.source_id in evidence
    assert FLETCHER_1986.source_id in evidence
    assert evidence[NUMA_INTRATHORACIC_1996.source_id].doi == (
        "10.1152/jappl.1996.80.5.1485"
    )
    assert evidence[FLETCHER_1986.source_id].doi == (
        "10.1213/00000539-198606000-00014"
    )

    constant_sources = {constant.provenance for constant in equation.constants}
    assert constant_sources == {NUMA_INTRATHORACIC_1996, FLETCHER_1986}


def test_williams_profile_provenance_is_descriptive_not_computational():
    assert WILLIAMS_TERM_CONTROL_2022.classification is (
        ParameterClassification.MEASURED_EMPIRICAL
    )
    assert WILLIAMS_TERM_CONTROL_2022.doi == "10.1038/s41390-021-01388-8"
    context = WILLIAMS_TERM_CONTROL_2022.context.lower()
    assert "medians and iqrs" in context
    assert "not algebraically decomposable" in context
    assert "individual patient-only" in context


def test_public_composite_name_does_not_overclaim_healthy_population():
    import paeddeadspace as pds

    assert hasattr(pds, "NumaFletcherCompositeReference")
    assert hasattr(pds, "numa_fletcher_composite_reference")
    assert not hasattr(pds, "HealthyIntubatedCompositeReference")
    assert not hasattr(pds, "healthy_intubated_composite_reference")
    context = FLETCHER_1986.context.lower()
    assert "normal pulmonary circulation is not equivalent to a healthy source population" in context


def test_williams_context_does_not_overclaim_generic_healthy_neonates():
    context = WILLIAMS_TERM_CONTROL_2022.context.lower()
    assert "without underlying respiratory disease" in context
    assert "poor perinatal adaptation" in context
    assert "not a generic healthy-neonate cohort" in context
