"""Deterministic scenarios evaluated through the installed audited core."""

from __future__ import annotations

from typing import Any

import paeddeadspace as pds

ScenarioRow = dict[str, Any]

WEIGHTS_KG = (2.0, 3.0, 5.0, 10.0, 20.0, 30.0)
GRID_VT_ML_KG = (4.0, 5.0, 6.0, 8.0)
GRID_APPARATUS_ML = (0.0, 2.0, 4.0, 8.0, 12.0, 22.0, 30.0, 55.0)
PATIENT_VD_VT_ASSUMPTION = 0.30
RR_ASSUMPTION_BPM = 20.0

PEARSALL_DOI = "10.1213/ANE.0000000000000148"
CHAU_DOI = "10.1111/j.1460-9592.2006.01895.x"
KWON_DOI = "10.4097/kjae.2012.62.5.418"
CAMPOS_DOI = "10.1111/pan.14724"
PROVENTIPED_DOI = "10.1097/EJA.0000000000001832"

PEARSALL_SOURCE = pds.EvidenceSource(
    source_id="PEARSALL_2014",
    citation="Pearsall MF, Feldman JM. Anesth Analg. 2014;118:776-780.",
    context=(
        "Named mathematical benchmark: 2-17 kg / 0-36 months, VT 8 mL/kg, "
        "patient physiologic VD/VT 0.30, RR 20/min; apparatus device volumes "
        "in the source ranged 8-55 mL."
    ),
    doi=PEARSALL_DOI,
)

CHAU_SOURCE = pds.EvidenceSource(
    source_id="CHAU_2006",
    citation="Chau A et al. Paediatr Anaesth. 2006;16:932-938.",
    context=(
        "Twenty healthy intubated children <2 years; a 22 mL airway filter was "
        "introduced and RR was adjusted to restore ETCO2 to 35 mmHg."
    ),
    doi=CHAU_DOI,
)

KWON_SOURCE = pds.EvidenceSource(
    source_id="KWON_2012",
    citation="Kwon MA. Korean J Anesthesiol. 2012;62:418-422.",
    context=(
        "Twenty healthy pediatric anesthesia patients studied with and without "
        "a pediatric HME with reported internal volume 22 mL."
    ),
    doi=KWON_DOI,
)

CAMPOS_SOURCE = pds.EvidenceSource(
    source_id="CAMPOS_2023",
    citation="Campos MD et al. Pediatr Anaesth. 2023;33:973-982.",
    context=(
        "Bench simulation at 2, 2.5 and 3 kg; VT 8 mL/kg; RR 40, 35 and "
        "30/min respectively; additional apparatus dead space 4 mL."
    ),
    doi=CAMPOS_DOI,
)

PROVENTIPED_SOURCE = pds.EvidenceSource(
    source_id="PROVENTIPED_2023",
    citation="Gardon A et al. Eur J Anaesthesiol. 2023;40:495-500.",
    context=(
        "External cohort-level plausibility reference: normocapnic alveolar "
        "minute ventilation 68 ± 21 mL/kg/min."
    ),
    doi=PROVENTIPED_DOI,
)

PEARSALL_DIRECT_APPARATUS_PROVENANCE = pds.Provenance(
    classification=pds.ParameterClassification.MEASURED_EMPIRICAL,
    source_id="PEARSALL_2014_SAMPLE_APPARATUS_30ML",
    citation=PEARSALL_SOURCE.citation,
    context=(
        "The source sample uses 30 mL cumulative apparatus volume "
        "(8 mL elbow + 22 mL filter in the commonly described setup). "
        "This is source benchmark/device-volume provenance, not proof that "
        "internal volume universally equals functional dead space."
    ),
    doi=PEARSALL_DOI,
    evidence_sources=(PEARSALL_SOURCE,),
)

PLUS22_PROVENANCE = pds.Provenance(
    classification=pds.ParameterClassification.MEASURED_EMPIRICAL,
    source_id="CHAU_2006_KWON_2012_22ML",
    citation="Chau 2006 airway filter; Kwon 2012 pediatric HME",
    context=(
        "Both studies report a 22 mL apparatus perturbation. Chau used a "
        "22 mL airway filter; Kwon reports a pediatric HME internal volume "
        "of 22 mL. Sharing the same numerical volume does not establish "
        "functional equivalence between devices."
    ),
    evidence_sources=(CHAU_SOURCE, KWON_SOURCE),
)

CAMPOS_PLUS4_PROVENANCE = pds.Provenance(
    classification=pds.ParameterClassification.MEASURED_EMPIRICAL,
    source_id="CAMPOS_2023_PLUS4ML",
    citation=CAMPOS_SOURCE.citation,
    context=(
        "The bench simulation explicitly compared baseline ventilation with "
        "and without an additional 4 mL apparatus dead space."
    ),
    doi=CAMPOS_DOI,
    evidence_sources=(CAMPOS_SOURCE,),
)

EXPLORATORY_APPARATUS_PROVENANCE = pds.Provenance(
    classification=pds.ParameterClassification.ASSUMPTION,
    source_id="VALIDATION_EXPLORATORY_APPARATUS_SWEEP",
    citation="PaedDeadSpace pre-specified validation/sensitivity grid",
    context=(
        "Synthetic exploratory apparatus values used to characterize model "
        "behavior. They are not claimed to be measured functional dead space."
    ),
)


def _source_fields(
    source_id: str,
    source_doi: str,
    source_context: str,
) -> ScenarioRow:
    return {
        "source_id": source_id,
        "source_doi": source_doi,
        "source_context": source_context,
    }


def _component(
    name: str,
    volume_ml: float,
    qualification: str,
    provenance: pds.Provenance,
) -> pds.ApparatusComponent:
    return pds.ApparatusComponent(
        name=name,
        dead_space_ml=volume_ml,
        active=True,
        provenance=provenance,
        qualification=qualification,
    )


def _state(
    weight_kg: float,
    vt_ml_kg: float,
    rr_bpm: float,
    apparatus_ml: float,
    *,
    pearsall_model: bool = False,
    apparatus_provenance: pds.Provenance = EXPLORATORY_APPARATUS_PROVENANCE,
) -> ScenarioRow:
    """Build one state using only public functions from the audited core."""
    vt_ml = pds.calculate_tidal_volume_ml(weight_kg, vt_ml_kg=vt_ml_kg)
    patient_model = (
        pds.PearsallBenchmarkPatientDeadSpace()
        if pearsall_model
        else pds.UserDefinedPatientVdVt(PATIENT_VD_VT_ASSUMPTION)
    )
    patient_vd_ml = pds.patient_dead_space_excluding_apparatus_ml(
        vt_ml, patient_model
    )
    apparatus_vd_ml = pds.apparatus_stack_dead_space_ml(
        (
            _component(
                "scenario apparatus",
                apparatus_ml,
                (
                    "Numerical apparatus volume specified by the named source "
                    "or exploratory sweep; functional equivalence is not generalized"
                ),
                apparatus_provenance,
            ),
        )
    )
    total_vd_ml = pds.total_dead_space_ml(patient_vd_ml, apparatus_vd_ml)
    static = {
        "vt_ml": vt_ml,
        "patient_vd_ml": patient_vd_ml,
        "apparatus_ds_ml": apparatus_vd_ml,
        "apparatus_ds_percent_vt": pds.apparatus_dead_space_percent_vt(
            apparatus_vd_ml, vt_ml
        ),
        "total_vd_ml": total_vd_ml,
    }

    try:
        total_vd_vt = pds.dead_space_fraction(total_vd_ml, vt_ml)
        alveolar_vt_ml = pds.alveolar_tidal_volume_ml(vt_ml, total_vd_ml)
        alveolar_ve_ml_min = pds.alveolar_minute_ventilation_ml_min(
            rr_bpm, alveolar_vt_ml
        )
    except pds.NonPhysicalStateError as exc:
        return {
            **static,
            "status": "model_breakdown",
            "status_reason": str(exc),
        }

    return {
        **static,
        "status": "physical",
        "status_reason": "",
        "total_vd_vt": total_vd_vt,
        "alveolar_vt_ml": alveolar_vt_ml,
        "alveolar_ve_ml_min": alveolar_ve_ml_min,
    }


def _comparison_metrics(
    baseline: ScenarioRow,
    current: ScenarioRow,
    rr_bpm: float,
) -> ScenarioRow:
    if current["status"] != "physical":
        return {
            "baseline_alveolar_ve_ml_min": baseline["alveolar_ve_ml_min"],
            "baseline_total_vd_vt": baseline["total_vd_vt"],
            "evaluation": "not_assessed",
        }

    baseline_ve = float(baseline["alveolar_ve_ml_min"])
    current_ve = float(current["alveolar_ve_ml_min"])
    burden = pds.relative_co2_burden(baseline_ve, current_ve)
    rr_required = pds.rr_required_to_preserve_alveolar_ventilation(
        baseline_ve,
        float(current["vt_ml"]),
        float(current["total_vd_ml"]),
    )
    return {
        "baseline_alveolar_ve_ml_min": baseline_ve,
        "baseline_total_vd_vt": baseline["total_vd_vt"],
        "change_total_vd_vt": (
            float(current["total_vd_vt"]) - float(baseline["total_vd_vt"])
        ),
        "change_apparatus_ds_percent_vt": current["apparatus_ds_percent_vt"],
        "alveolar_ve_ratio": current_ve / baseline_ve,
        "relative_co2_burden": burden,
        "rr_required_bpm": rr_required,
        "rr_multiplier": rr_required / rr_bpm,
    }


def pearsall_direct_benchmark() -> ScenarioRow:
    """Reproduce the published ~43/min endpoint with the audited core surrogate."""
    baseline = _state(
        10.0, 8.0, 20.0, 0.0,
        pearsall_model=True,
        apparatus_provenance=PEARSALL_DIRECT_APPARATUS_PROVENANCE,
    )
    current = _state(
        10.0, 8.0, 20.0, 30.0,
        pearsall_model=True,
        apparatus_provenance=PEARSALL_DIRECT_APPARATUS_PROVENANCE,
    )
    metrics = _comparison_metrics(baseline, current, 20.0)
    required_rr = float(metrics["rr_required_bpm"])
    preservation_rr = 1120.0 / 26.0
    passed = abs(required_rr - preservation_rr) <= 1e-9 and abs(required_rr - 43.0) <= 0.1
    return {
        "scenario_id": "pearsall_direct_10kg_30ml",
        "scenario_family": "pearsall_direct",
        "scenario_class": "quantitative_benchmark",
        **_source_fields(
            PEARSALL_SOURCE.source_id,
            PEARSALL_DOI,
            PEARSALL_SOURCE.context,
        ),
        "provenance_rationale": (
            "Published Pearsall sample: 10 kg, VT 80 mL, patient VD/VT 0.30, "
            "RR 20/min and 30 mL apparatus; source reports required RR "
            "approximately 43/min."
        ),
        "assumption_label": (
            "Named Pearsall patient-VD benchmark; patient VD excludes apparatus"
        ),
        "benchmark_method": (
            "Audited core preserves the sample's baseline alveolar ventilation. "
            "This reproduces the published rounded endpoint (~43/min) but is "
            "not a reimplementation of Pearsall Equation 7."
        ),
        "published_reference_rr_bpm": 43.0,
        "expected_result": (
            "Published endpoint approximately 43/min; core preservation "
            "calculation 1120/26 = 43.0769/min"
        ),
        "evaluation": "pass" if passed else "fail",
        "weight_kg": 10.0,
        "vt_ml_kg": 8.0,
        "rr_bpm": 20.0,
        "patient_vd_vt_assumption": 0.30,
        "apparatus_baseline_ml": 0.0,
        "apparatus_increment_ml": 30.0,
        **current,
        **metrics,
    }


def pearsall_sensitivity_rows() -> list[ScenarioRow]:
    """Synthetic 0--55 mL sweep under named Pearsall assumptions."""
    baseline = _state(10.0, 8.0, 20.0, 0.0, pearsall_model=True)
    rows: list[ScenarioRow] = []
    for apparatus_ml in range(56):
        current = _state(
            10.0,
            8.0,
            20.0,
            float(apparatus_ml),
            pearsall_model=True,
            apparatus_provenance=EXPLORATORY_APPARATUS_PROVENANCE,
        )
        metrics = _comparison_metrics(baseline, current, 20.0)
        mechanistic_paco2 = None
        if current["status"] == "physical":
            mechanistic_paco2 = pds.baseline_calibrated_paco2_mechanistic_mmHg(
                40.0,
                float(baseline["alveolar_ve_ml_min"]),
                float(current["alveolar_ve_ml_min"]),
            )
        rows.append(
            {
                "scenario_id": f"pearsall_sweep_{apparatus_ml:02d}ml",
                "scenario_family": "pearsall_sensitivity",
                "scenario_class": "exploratory_sensitivity",
                **_source_fields(
                    PEARSALL_SOURCE.source_id,
                    PEARSALL_DOI,
                    PEARSALL_SOURCE.context,
                ),
                "provenance_rationale": (
                    "Synthetic integer apparatus sweep under the named Pearsall "
                    "sample assumptions. The source used 0 mL baseline and "
                    "typical device arrangements within an 8-55 mL range; not "
                    "every integer sweep value is a measured device."
                ),
                "assumption_label": (
                    "Pearsall patient-only VD/VT 0.30 and RR 20/min; explicitly "
                    "supplied baseline PaCO2 40 mmHg for mechanistic calibration"
                ),
                "benchmark_method": "Exploratory sensitivity only",
                "expected_result": "",
                "evaluation": "not_assessed",
                "weight_kg": 10.0,
                "vt_ml_kg": 8.0,
                "rr_bpm": 20.0,
                "patient_vd_vt_assumption": 0.30,
                "apparatus_baseline_ml": 0.0,
                "apparatus_increment_ml": float(apparatus_ml),
                "paco2_baseline_mmHg": 40.0,
                "paco2_mechanistic_mmHg": mechanistic_paco2,
                **current,
                **metrics,
            }
        )
    return rows


def plus22_directionality_rows() -> list[ScenarioRow]:
    """Chau/Kwon-inspired +22 mL directionality family."""
    rows: list[ScenarioRow] = []
    combined_context = (
        f"{CHAU_SOURCE.context} {KWON_SOURCE.context} "
        "The same numerical 22 mL perturbation is used here only for "
        "directionality/scaling; exact device functional equivalence is not assumed."
    )
    for weight_kg in WEIGHTS_KG:
        for vt_ml_kg in (6.0, 8.0):
            baseline = _state(weight_kg, vt_ml_kg, 20.0, 0.0)
            current = _state(
                weight_kg,
                vt_ml_kg,
                20.0,
                22.0,
                apparatus_provenance=PLUS22_PROVENANCE,
            )
            metrics = _comparison_metrics(baseline, current, 20.0)
            if current["status"] == "physical":
                direction_ok = (
                    float(current["alveolar_ve_ml_min"])
                    < float(baseline["alveolar_ve_ml_min"])
                    and float(metrics["relative_co2_burden"]) > 1.0
                )
                metrics["evaluation"] = "pass" if direction_ok else "fail"
            rows.append(
                {
                    "scenario_id": f"plus22_{weight_kg:g}kg_{vt_ml_kg:g}mlkg",
                    "scenario_family": "chau_kwon_plus22",
                    "scenario_class": "directionality_check",
                    **_source_fields(
                        "CHAU_2006;KWON_2012",
                        f"{CHAU_DOI};{KWON_DOI}",
                        combined_context,
                    ),
                    "provenance_rationale": (
                        "+22 mL is source-derived: Chau used a 22 mL airway "
                        "filter; Kwon reports a 22 mL HME internal volume. "
                        "The present scenarios test only directionality/scaling."
                    ),
                    "assumption_label": (
                        "Patient-only VD/VT 0.30 and RR 20/min are explicitly "
                        "inherited from Pearsall for sensitivity, not defaults"
                    ),
                    "benchmark_method": "Directionality check; no exact clinical fit",
                    "expected_result": (
                        "For physical states, alveolar ventilation decreases and "
                        "relative CO2 burden increases"
                    ),
                    "weight_kg": weight_kg,
                    "vt_ml_kg": vt_ml_kg,
                    "rr_bpm": 20.0,
                    "patient_vd_vt_assumption": 0.30,
                    "apparatus_baseline_ml": 0.0,
                    "apparatus_increment_ml": 22.0,
                    **current,
                    **metrics,
                }
            )
    return rows


def campos_neonatal_rows() -> list[ScenarioRow]:
    """Campos-inspired +4 mL neonatal sensitivity at source RR/weight settings."""
    source_cases = (
        (2.0, 40.0, 0.51, 0.68),
        (2.5, 35.0, 0.43, 0.62),
        (3.0, 30.0, 0.38, 0.60),
    )
    rows: list[ScenarioRow] = []
    for weight_kg, rr_bpm, source_baseline_vd_vt, source_plus4_vd_vt in source_cases:
        baseline = _state(weight_kg, 8.0, rr_bpm, 0.0)
        current = _state(
            weight_kg,
            8.0,
            rr_bpm,
            4.0,
            apparatus_provenance=CAMPOS_PLUS4_PROVENANCE,
        )
        metrics = _comparison_metrics(baseline, current, rr_bpm)
        direction_ok = (
            current["status"] == "physical"
            and float(metrics["alveolar_ve_ratio"]) < 1.0
            and float(metrics["relative_co2_burden"]) > 1.0
            and float(metrics["rr_multiplier"]) > 1.0
        )
        metrics["evaluation"] = "pass" if direction_ok else "fail"
        rows.append(
            {
                "scenario_id": f"campos_plus4_{weight_kg:g}kg",
                "scenario_family": "campos_neonatal_plus4",
                "scenario_class": "directionality_check",
                **_source_fields(
                    CAMPOS_SOURCE.source_id,
                    CAMPOS_DOI,
                    CAMPOS_SOURCE.context,
                ),
                "provenance_rationale": (
                    "Source-faithful weight, VT, RR and +4 mL apparatus setup "
                    "for directionality. Patient-only VD/VT remains the explicit "
                    "Pearsall-derived sensitivity assumption, so the source "
                    "airway-VD/VT values are contextual only."
                ),
                "assumption_label": (
                    "VT 8 mL/kg and source RR; patient-only VD/VT 0.30 is an "
                    "explicit sensitivity assumption, not Campos-derived"
                ),
                "benchmark_method": (
                    "Directionality/sensitivity only; source airway VD/VT ratios "
                    "are not used to fit the model"
                ),
                "source_reference_baseline_vd_vt": source_baseline_vd_vt,
                "source_reference_with_apparatus_vd_vt": source_plus4_vd_vt,
                "expected_result": (
                    "Lower alveolar ventilation and higher relative CO2 burden; "
                    "not exact capnogram/rebreathing or airway-VD/VT reproduction"
                ),
                "weight_kg": weight_kg,
                "vt_ml_kg": 8.0,
                "rr_bpm": rr_bpm,
                "patient_vd_vt_assumption": 0.30,
                "apparatus_baseline_ml": 0.0,
                "apparatus_increment_ml": 4.0,
                **current,
                **metrics,
            }
        )
    return rows


def general_sensitivity_grid_rows() -> list[ScenarioRow]:
    """Generate the complete weight x VT x apparatus exploratory grid."""
    rows: list[ScenarioRow] = []
    for weight_kg in WEIGHTS_KG:
        for vt_ml_kg in GRID_VT_ML_KG:
            baseline = _state(weight_kg, vt_ml_kg, RR_ASSUMPTION_BPM, 0.0)
            for apparatus_ml in GRID_APPARATUS_ML:
                current = _state(
                    weight_kg,
                    vt_ml_kg,
                    RR_ASSUMPTION_BPM,
                    apparatus_ml,
                    apparatus_provenance=EXPLORATORY_APPARATUS_PROVENANCE,
                )
                metrics = _comparison_metrics(baseline, current, RR_ASSUMPTION_BPM)
                rows.append(
                    {
                        "scenario_id": (
                            f"grid_{weight_kg:g}kg_{vt_ml_kg:g}mlkg_"
                            f"{apparatus_ml:g}ml"
                        ),
                        "scenario_family": "general_grid",
                        "scenario_class": "exploratory_sensitivity",
                        **_source_fields(
                            "PAEDDEADSPACE_PREDEFINED_GRID",
                            "",
                            "Pre-specified exploratory sensitivity grid; not an external dataset.",
                        ),
                        "provenance_rationale": (
                            "Pre-specified deterministic weight, VT and apparatus "
                            "grid for model-behavior exploration."
                        ),
                        "assumption_label": (
                            "Patient-only VD/VT 0.30 is an explicit sensitivity "
                            "assumption inherited from Pearsall, not a default; "
                            "RR 20/min is an arithmetic normalization"
                        ),
                        "benchmark_method": "Exploratory sensitivity only",
                        "expected_result": "",
                        "evaluation": "not_assessed",
                        "weight_kg": weight_kg,
                        "vt_ml_kg": vt_ml_kg,
                        "rr_bpm": RR_ASSUMPTION_BPM,
                        "patient_vd_vt_assumption": 0.30,
                        "apparatus_baseline_ml": 0.0,
                        "apparatus_increment_ml": apparatus_ml,
                        **current,
                        **metrics,
                    }
                )
    return rows


def proventiped_reference_row() -> ScenarioRow:
    """Return a reference-only cohort value without constructing a model case."""
    return {
        "scenario_id": "proventiped_external_reference",
        "scenario_family": "proventiped_reference",
        "scenario_class": "plausibility_reference",
        **_source_fields(
            PROVENTIPED_SOURCE.source_id,
            PROVENTIPED_DOI,
            PROVENTIPED_SOURCE.context,
        ),
        "provenance_rationale": (
            "Published cohort-level normocapnic alveolar minute ventilation "
            "retained as an external descriptive reference only."
        ),
        "assumption_label": "External descriptive reference only; no model tuning",
        "benchmark_method": "External plausibility reference only",
        "status": "reference_only",
        "status_reason": (
            "No independently specified patient-level case is available for validation"
        ),
        "expected_result": "",
        "evaluation": "not_assessed",
        "reference_value": 68.0,
        "reference_sd": 21.0,
        "reference_units": "mL/kg/min",
    }


def generate_all_rows() -> list[ScenarioRow]:
    """Return all deterministic validation, reference, and exploration rows."""
    return [
        pearsall_direct_benchmark(),
        *pearsall_sensitivity_rows(),
        *plus22_directionality_rows(),
        *campos_neonatal_rows(),
        *general_sensitivity_grid_rows(),
        proventiped_reference_row(),
    ]
