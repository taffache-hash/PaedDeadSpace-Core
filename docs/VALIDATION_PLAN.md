# PaedDeadSpace v1.0.0 validation and exploration plan

## Separation from the scientific core

The installed `paeddeadspace` package remains the read-only scientific source
of truth. This validation layer constructs deterministic scenarios, calls only
public core functions, records outputs and generates figures. It does not
modify the core, add disease mode, or implement an absolute VCO2/VA PaCO2
equation.

## Evidence classes

Each CSV row is explicitly one of:

1. `quantitative_benchmark` — a published/source endpoint can be checked
   numerically, with the method used by this runner stated explicitly.
2. `directionality_check` — the external study supports direction/scaling, but
   the one-compartment model and available source data do not justify exact
   patient-level reproduction.
3. `plausibility_reference` — external cohort information retained as context,
   with no fitting or pass/fail.
4. `exploratory_sensitivity` — pre-specified model-behavior sweeps, not
   external validation.

Source-derived apparatus volumes are classified as measured/empirical source
inputs. Synthetic sweep values remain assumptions. Neither classification
implies that internal/geometric apparatus volume universally equals functional
dead space.

## Pearsall endpoint benchmark

Source: Pearsall MF, Feldman JM. Anesth Analg. 2014;118:776-780.
DOI: 10.1213/ANE.0000000000000148.

Published sample:
- 10 kg
- VT 8 mL/kg = 80 mL
- patient physiologic VD/VT 0.30
- patient VD 24 mL
- apparatus 30 mL
- cumulative VD 54 mL
- RR required to maintain PaCO2 40 reported as approximately 43/min.

The audited core deliberately does not implement the source's absolute PaCO2
path. Therefore the validation runner uses preservation of the sample's
baseline alveolar ventilation: `20 × (80 - 24) = 1120 mL/min`; after apparatus,
`VT - VD = 26 mL`, so RR = `1120/26 = 43.0769/min`.

This is a quantitative **endpoint reproduction** of the published rounded
~43/min result, not an exact reimplementation of Pearsall Equation 7. The
distinction is retained in the CSV and report.

The 0-55 mL curve is a synthetic sensitivity sweep under named Pearsall
assumptions. It is not a set of 56 measured device configurations.

## Chau / Kwon +22 mL directionality

Chau 2006 DOI: 10.1111/j.1460-9592.2006.01895.x.
Kwon 2012 DOI: 10.4097/kjae.2012.62.5.418.

Chau introduced a 22 mL airway filter in healthy intubated children <2 years
and adjusted RR to restore ETCO2. Kwon compared a pediatric HME with reported
internal volume 22 mL versus removal.

The runner uses +22 mL for directionality and body-size scaling only. It does
not assume identical functional behavior between the two devices and does not
fit the source clinical outcomes.

## Campos neonatal +4 mL directionality

Source: Campos MD et al. Pediatr Anaesth. 2023;33:973-982.
DOI: 10.1111/pan.14724.

The source bench simulation used:
- 2 kg: VT 8 mL/kg, RR 40/min
- 2.5 kg: VT 8 mL/kg, RR 35/min
- 3 kg: VT 8 mL/kg, RR 30/min
- +4 mL apparatus dead space.

The source reported airway-VD/VT changes of approximately 0.51→0.68,
0.43→0.62 and 0.38→0.60 respectively. The validation runner preserves the
source weight/VT/RR/+4 setup but retains patient-only VD/VT=0.30 as an explicit
Pearsall-derived sensitivity assumption. Therefore the source airway-VD/VT
values are context, not fitting targets.

## General grid

Weights: 2, 3, 5, 10, 20, 30 kg.
VT: 4, 5, 6, 8 mL/kg.
Apparatus: 0, 2, 4, 8, 12, 22, 30, 55 mL.
Patient-only VD/VT: 0.30 explicitly as a Pearsall-inherited sensitivity
assumption, not a universal default.
RR: 20/min as arithmetic normalization.

States with total VD >= VT are emitted as model-breakdown rows. They are not
silently dropped and are not clinical thresholds.

## PROVENTIPED

Source: Gardon A et al. Eur J Anaesthesiol. 2023;40:495-500.
DOI: 10.1097/EJA.0000000000001832.

Normocapnic alveolar minute ventilation approximately 68 ± 21 mL/kg/min is
retained only as an external cohort-level plausibility reference. No constant
is tuned to 68 and no pass/fail case is constructed to equal it.

## Unresolved scientific issues

- P11 remains unresolved: no audited universal patient physiologic VD/VT
  default exists for an intubated pediatric patient.
- Apparatus geometric/internal volume may differ from effective functional
  dead space.
- Measured clinical VD/VT may already include apparatus depending on method and
  setup; it must not be entered into the patient-only field without
  scientifically justified decomposition.
- Dynamic rebreathing, leaks, compliance, circuit compression, timing,
  capnogram morphology, V/Q heterogeneity and metabolic adaptation are outside
  this one-compartment validation layer.
- Near VD=VT, normalized outputs diverge mathematically. This is model behavior,
  not a clinical prediction.
