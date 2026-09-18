# PaedDeadSpace — Engine Specification v1
Version: 2026-09-18

## Purpose
Open-source educational/exploratory model of pediatric apparatus dead-space burden during mechanical ventilation.
Not patient-specific clinical decision support.

## Non-negotiable provenance rule
Every engine parameter must be explicitly classified as one of:
1. measured/empirical
2. derived
3. assumption
4. user-defined

No hidden “reasonable” constants.

## v1 core inputs
- `weight_kg`: user-defined, >0
- `age_years`: user-defined, >=0
- `vt_ml_kg` or `vt_ml`: user-defined
- `rr_bpm`: user-defined, >0
- optional `paco2_baseline_mmHg`
- optional `paco2_target_mmHg`
- apparatus stack as explicit components with `dead_space_ml`
- explicit patient dead-space model selection

## VT presets
Evidence-informed quick presets:
- 5, 6, 8 mL/kg: principal pediatric exploratory grid
- 4 mL/kg: low-VT sensitivity/stress-test except age-appropriate neonatal use
- 10 mL/kg: historical comparator

Do not present presets as therapeutic recommendations.

## Patient dead space
### Numa anatomic scaling
`ds_total_ml_kg = 3.28 - 0.56 * ln(1 + age_years)`

This is TOTAL ANATOMIC dead space, not an automatic physiologic-dead-space default in an intubated child.
Numa also reports mean intrathoracic anatomic dead space of approximately 1.03 mL/kg.

### v1 blocker
There is currently no single literature-supported universal default for intubated pediatric physiologic dead space.

Therefore v1 must:
- require an explicit model mode;
- support user-defined baseline `VD/VT` as a transparent sensitivity/benchmark mode;
- optionally support a transparent anatomic-component mode once its assumptions are explicitly locked;
- never silently map Numa total anatomic dead space to physiologic VD.

Pearsall’s `VD/VT = 0.30` is allowed only as a named benchmark assumption.

## Apparatus dead space
- Always allow generic numeric apparatus dead-space entry in mL.
- Apparatus stack total = sum of active component volumes.
- Preserve provenance for every component.
- Do not equate manufacturer internal/geometric volume with functional dead space without qualification.

## Core derived variables
- `vt_ml = weight_kg * vt_ml_kg` if VT entered per kg
- `vd_total_ml = selected_patient_vd_ml + apparatus_stack_ml [+ disease_alveolar_vd_ml only in future disease mode]`
- `vd_vt = vd_total_ml / vt_ml`
- `alveolar_vt_ml = vt_ml - vd_total_ml`
- `alveolar_ve_ml_min = rr_bpm * alveolar_vt_ml`

If `vd_total_ml >= vt_ml`, standard one-compartment output must be flagged as model breakdown / non-physical zone, not silently calculated.

## VCO2 models
### Primary candidate
Lindahl BJA 1989:
`vco2_ml_min = 4.8 * weight_kg + 6.4`

Context: anesthetized surgical children.

### Alternative sensitivity model
Lindahl et al., Can J Anaesth 1989:
`X = ln(weight_kg)`
`vco2_ml_min = -1.25 * X + 13.0 * X**2`

Source context: spontaneously breathing anesthetized infants/children, source weight range 2.8–26.5 kg.

### Pending-full-text sensitivity evidence
Lindahl, Hulse & Hatch 1984:
controlled-ventilation VCO2 approximately `6.3 ± 1.6 mL/min/kg` in publisher abstract.
Do not use as sole default until full-text audit.

### Prior-art benchmark model
Pearsall 2014 / Brody:
`vco2_ml_min = 5.56 * weight_kg**1.05`
Use only in named Pearsall benchmark mode (0–36 months / 2–17 kg context).

## CO2 outputs
### Robust normalized output
Under stable VCO2:
`relative_co2_burden = VA_baseline / VA_current`

### Baseline-calibrated PaCO2
If baseline PaCO2 and baseline alveolar ventilation are known:
`paco2_new = paco2_baseline * VA_baseline / VA_current`

Label as a mechanistic estimate, not patient-level prediction.

### Absolute PaCO2
Do not make the absolute VCO2/VA equation a default until unit conventions (mL/L, STPD/BTPS, pressure constant) are explicitly tested.
Coss-Bu reports:
`VE = 0.863 * VCO2 / [PaCO2 * (1 - VD/VT)]`
This can be used for unit-validation tests.

## Compensatory RR
Primary v1 output:
`rr_required = VA_baseline / (vt_new_ml - vd_new_ml)`

Only compute if denominator >0.

## Warning/display metrics
- apparatus dead space as % of VT
- total VD/VT
- VT / apparatus-dead-space ratio
- explicit warning if VD >= VT

Do not invent a universal danger threshold.

Optional neonatal bench warning:
Takahashi 2026 found VTe/dead-space ratio >1.82 strongly predicted reliable ETCO2 in that bench setup.
Never present 1.82 as a universal pediatric threshold.

## Disease mode
Out of baseline v1.

Coss-Bu 2003 is validation/future-module evidence:
- mean VD/VT 0.48 ± 0.20
- ARDS 0.62 ± 0.14
- non-ARDS 0.43 ± 0.15

Do not import these into healthy/anesthetized baseline defaults.

## Validation tests required before UI work
1. Pearsall 2014 benchmark mode:
   - VT 8 mL/kg
   - VD/VT 0.30
   - RR 20/min
   - Brody VCO2
   - apparatus DS 8–55 mL
   - reproduce published sample calculation direction/magnitude

2. Chau 2006:
   - +22 mL airway filter
   - compensatory RR must increase

3. Kwon 2012:
   - 22 mL HME
   - model must show greater CO2 burden at lower weights
   - empirical PaCO2 changed from 46.1 ± 6.9 to 37.9 ± 4.3 mmHg after HME removal

4. PROVENTIPED:
   - normocapnic alveolar minute ventilation plausibility target ≈ 68 ± 21 mL/kg/min
   - validation target only, not hard-coded constant

5. Williams 2022 starter volumes:
   - Capnostat-5: 0.8 mL
   - ETT 2.0 mm: 1.2 mL
   - ETT 2.5 mm: 1.8 mL
   - ETT 3.0 mm: 2.0 mL
   - ETT 3.5 mm: 3.0 mL
   - ETT 4.0 mm: 3.2 mL

6. Campos 2023:
   - qualitative neonatal sensitivity to +4 mL apparatus dead space at 2–3 kg and VT 8 mL/kg
   - exact capnogram/rebreathing reproduction is NOT expected from v1

## Coding constraints
- Python core first.
- No web UI until unit tests and benchmark tests pass.
- Separate pure physiology functions from presentation.
- Typed data models.
- No magic numbers.
- Every empirical constant must have a source identifier in code/comments or structured provenance metadata.
- Deterministic unit tests.
- Functions should fail clearly on non-physical input.
- Keep disease mode disabled.
- Keep absolute PaCO2 experimental until unit audit passes.

## Primary DOI references
- Numa 1996: https://doi.org/10.1152/jappl.1996.80.5.1485
- Pearsall 2014: https://doi.org/10.1213/ANE.0000000000000148
- Lindahl BJA 1989: https://doi.org/10.1093/bja/62.1.70
- Lindahl CJA 1989: https://doi.org/10.1007/BF03011430
- Lindahl 1984: https://doi.org/10.1111/j.1399-6576.1984.tb02010.x
- PROVENTIPED 2023: https://doi.org/10.1097/EJA.0000000000001832
- Spaeth 2022: https://doi.org/10.1111/pan.14366
- Chau 2006: https://doi.org/10.1111/j.1460-9592.2006.01895.x
- Kwon 2012: https://doi.org/10.4097/kjae.2012.62.5.418
- Williams 2022: https://doi.org/10.1038/s41390-021-01388-8
- Campos 2023: https://doi.org/10.1111/pan.14724
- Coss-Bu 2003: https://doi.org/10.1378/chest.123.6.2050
- Takahashi 2026: https://doi.org/10.1038/s41390-026-05122-0
