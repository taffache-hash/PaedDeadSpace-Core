from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import pytest

import paeddeadspace
from validation import scenarios
from validation.reporting import (
    RESULT_FIELDS,
    write_results_csv,
    write_summary,
    write_validation_outputs,
)


def test_pearsall_endpoint_benchmark_is_approximately_43_per_minute():
    row = scenarios.pearsall_direct_benchmark()
    assert row["scenario_class"] == "quantitative_benchmark"
    assert row["rr_required_bpm"] == pytest.approx(1120.0 / 26.0)
    assert row["published_reference_rr_bpm"] == 43.0
    assert row["rr_required_bpm"] == pytest.approx(43.0, abs=0.1)
    assert "not a reimplementation" in row["benchmark_method"]
    assert row["evaluation"] == "pass"


def test_plus22_lowers_alveolar_ventilation_for_all_physical_states():
    physical = [
        row for row in scenarios.plus22_directionality_rows()
        if row["status"] == "physical"
    ]
    assert physical
    for row in physical:
        assert row["alveolar_ve_ml_min"] < row["baseline_alveolar_ve_ml_min"]
        assert row["evaluation"] == "pass"


def test_plus22_increases_relative_co2_burden_for_physical_states():
    physical = [
        row for row in scenarios.plus22_directionality_rows()
        if row["status"] == "physical"
    ]
    assert all(row["relative_co2_burden"] > 1.0 for row in physical)


def test_plus22_effect_is_stronger_at_lower_weight_in_comparable_physical_set():
    rows = {
        (row["weight_kg"], row["vt_ml_kg"]): row
        for row in scenarios.plus22_directionality_rows()
        if row["status"] == "physical"
    }
    low = rows[(5.0, 8.0)]
    high = rows[(10.0, 8.0)]
    assert low["relative_co2_burden"] > high["relative_co2_burden"] > 1.0
    assert low["rr_multiplier"] > high["rr_multiplier"] > 1.0


def test_source_derived_apparatus_provenance_is_not_misclassified_as_assumption():
    assert (
        scenarios.PLUS22_PROVENANCE.classification
        is paeddeadspace.ParameterClassification.MEASURED_EMPIRICAL
    )
    assert (
        scenarios.CAMPOS_PLUS4_PROVENANCE.classification
        is paeddeadspace.ParameterClassification.MEASURED_EMPIRICAL
    )
    assert (
        scenarios.EXPLORATORY_APPARATUS_PROVENANCE.classification
        is paeddeadspace.ParameterClassification.ASSUMPTION
    )
    assert scenarios.CHAU_DOI.endswith("01895.x")


def test_campos_rows_use_source_weight_rr_and_remain_sensitivity_checks():
    first = scenarios.campos_neonatal_rows()
    second = scenarios.campos_neonatal_rows()
    assert first == second
    assert [(row["weight_kg"], row["rr_bpm"]) for row in first] == [
        (2.0, 40.0),
        (2.5, 35.0),
        (3.0, 30.0),
    ]
    assert first[0]["apparatus_ds_percent_vt"] == pytest.approx(25.0)
    assert first[1]["apparatus_ds_percent_vt"] == pytest.approx(20.0)
    assert first[2]["apparatus_ds_percent_vt"] == pytest.approx(100.0 * 4.0 / 24.0)
    assert [row["source_reference_baseline_vd_vt"] for row in first] == [
        0.51, 0.43, 0.38
    ]
    assert [row["source_reference_with_apparatus_vd_vt"] for row in first] == [
        0.68, 0.62, 0.60
    ]
    for row in first:
        assert row["status"] == "physical"
        assert row["alveolar_ve_ratio"] < 1.0
        assert row["relative_co2_burden"] > 1.0
        assert row["rr_required_bpm"] > row["rr_bpm"]
        assert row["evaluation"] == "pass"
        assert row["scenario_class"] == "directionality_check"


def test_nonphysical_states_are_retained_and_labelled():
    rows = scenarios.generate_all_rows()
    breakdown = [row for row in rows if row["status"] == "model_breakdown"]
    assert breakdown
    by_family = Counter(row["scenario_family"] for row in breakdown)
    assert by_family["general_grid"] == 47
    assert by_family["chau_kwon_plus22"] == 5
    for row in breakdown:
        assert "model breakdown" in row["status_reason"]
        assert row["evaluation"] == "not_assessed"
        assert "alveolar_ve_ml_min" not in row
        assert "relative_co2_burden" not in row


def test_csv_generation_contains_required_columns_and_traceability(tmp_path):
    rows = scenarios.generate_all_rows()
    path = write_results_csv(rows, tmp_path / "validation_results.csv")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        written = list(reader)
    required = {
        "scenario_id",
        "scenario_class",
        "source_id",
        "source_doi",
        "source_context",
        "provenance_rationale",
        "status",
        "evaluation",
        "vt_ml",
        "patient_vd_ml",
        "apparatus_ds_ml",
        "total_vd_vt",
        "relative_co2_burden",
        "rr_multiplier",
    }
    assert required <= set(reader.fieldnames or ())
    assert required <= set(RESULT_FIELDS)
    assert written
    assert all(row["scenario_class"] for row in written)
    assert all(row["provenance_rationale"] for row in written)


def test_proventiped_is_reference_only_without_circular_pass_fail():
    row = scenarios.proventiped_reference_row()
    assert row["scenario_class"] == "plausibility_reference"
    assert row["reference_value"] == 68.0
    assert row["reference_sd"] == 21.0
    assert row["evaluation"] == "not_assessed"
    assert row["expected_result"] == ""
    assert "weight_kg" not in row
    assert "alveolar_ve_ml_min" not in row


def test_validation_imports_and_calls_the_installed_core(monkeypatch):
    assert scenarios.pds is paeddeadspace
    original = paeddeadspace.rr_required_to_preserve_alveolar_ventilation
    calls = []

    def observed(*args, **kwargs):
        calls.append((args, kwargs))
        return original(*args, **kwargs)

    monkeypatch.setattr(
        scenarios.pds, "rr_required_to_preserve_alveolar_ventilation", observed
    )
    scenarios.pearsall_direct_benchmark()
    assert calls


def test_requirements_do_not_try_to_install_validation_directory_as_core():
    requirements = (
        Path(__file__).resolve().parents[1] / "requirements-validation.txt"
    ).read_text(encoding="utf-8")
    assert "-e ." not in requirements


def test_summary_reports_breakdowns_by_correct_family(tmp_path):
    rows = scenarios.generate_all_rows()
    path = write_summary(rows, tmp_path / "summary.md")
    text = path.read_text(encoding="utf-8")
    assert "47" in text
    assert "general grid" in text
    assert "5" in text
    assert "+22 mL family" in text


def test_complete_runner_writes_expected_files(tmp_path):
    paths = write_validation_outputs(scenarios.generate_all_rows(), tmp_path)
    names = {path.name for path in paths}
    expected = {
        "validation_results.csv",
        "validation_summary.md",
        "pearsall_total_vd_vt.png",
        "pearsall_alveolar_ventilation.png",
        "pearsall_relative_co2.png",
        "pearsall_rr_required.png",
        "rr_multiplier_vs_apparatus_vt6.png",
        "relative_co2_vs_apparatus_vt6.png",
        "apparatus_percent_vt_vs_weight.png",
    }
    assert names == expected
    assert all(path.exists() and path.stat().st_size > 0 for path in paths)
