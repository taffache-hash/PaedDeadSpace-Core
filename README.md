# PaedDeadSpace-Core

[![Release](https://img.shields.io/badge/release-v1.0.0-blue)](https://github.com/taffache-hash/PaedDeadSpace-Core/releases/tag/v1.0.0)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://github.com/taffache-hash/PaedDeadSpace-Core/actions/workflows/tests.yml/badge.svg)](https://github.com/taffache-hash/PaedDeadSpace-Core/actions/workflows/tests.yml)
![Zenodo DOI](https://img.shields.io/badge/Zenodo%20DOI-pending-lightgrey)

**PaedDeadSpace: Pediatric Apparatus Dead-Space Explorer — Core** is the scientific Python engine for modeling pediatric apparatus dead-space burden, alveolar ventilation, and compensatory respiratory-rate requirements.

> For educational and research use only. Not intended for clinical decision-making or patient-specific treatment recommendations.

## Scientific scope
PaedDeadSpace separates patient dead space from apparatus dead space and explores how apparatus volume changes effective dead-space burden and modeled alveolar ventilation. The Core contains all scientific equations, provenance objects, input validation, model-boundary handling, and validation scenarios. The UI and Windows distributions consume this Core rather than duplicating the equations.

## Model assumptions
- One-compartment ventilation framework.
- Apparatus dead space is entered separately from patient dead space.
- Relative CO₂ burden and the compensatory RR multiplier use a fixed-VCO₂ assumption and are algebraically identical under that framework; they are not independent evidence.
- The Numa–Fletcher mode is an evidence-informed reference/sensitivity construction, not a universal healthy default.
- The Pearsall mode is a named reproducibility benchmark, not a physiologic default.
- If total effective dead space approaches or exceeds VT, the software reports model breakdown rather than an arbitrarily large RR.

## Known limitations
This model does not represent heterogeneous lung units, dynamic/recruitment physiology, disease-specific mechanics, spontaneous-breathing interactions, or patient-specific gas exchange. It does not calculate a routine absolute PaCO₂ target and has not been validated as a clinical decision-support system or medical device.

## Installation
Python **3.11–3.13** is the supported range for v1.0.0.

```bash
python -m pip install -e .
```

## Tests and validation
```bash
python -m pytest -q tests
python -m pip install -r requirements-validation.txt
PYTHONPATH=src:. python -m pytest -q validation_tests
PYTHONPATH=src:. python -m validation.run_validation
```

The frozen v1.0.0 release contains **47 Core tests** and **13 validation tests**. See [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## Golden Pearsall benchmark
Input: 10 kg, age 2 years, VT 8 mL/kg, RR 20/min, Pearsall benchmark patient VD/VT 0.30, apparatus dead space 30 mL.

Expected output: VT 80 mL; patient VD 24 mL; apparatus VD 30 mL; total VD 54 mL; total VD/VT 0.675 (67.5%); alveolar VT 26 mL; current alveolar ventilation 520 mL/min; no-added-apparatus baseline 1120 mL/min; relative CO₂ burden 2.154; RR required 43.08/min; RR multiplier 2.154.

This case is a **reproducibility benchmark, not a physiological default or treatment target**.

## Scientific documentation
- `docs/ENGINE_SPEC.md` — scientific architecture and equations
- `docs/PARAMETER_PROVENANCE.xlsx` — parameter-level provenance table
- `docs/REFERENCES.md` — bibliographic sources and DOI links
- `docs/VALIDATION_PLAN.md` and `validation_outputs/` — validation design and outputs

No copyrighted full-text articles are redistributed in this repository.

## Citation
GitHub will expose `CITATION.cff` through **Cite this repository**. The PaedDeadSpace-Core Zenodo DOI will be the preferred citation for the scientific project once assigned.

## Author
**Paolo Taffache** — ORCID: 0009-0002-8806-9733  
General and Pediatric Anesthesia and Intensive Care Unit, IRCCS AOU Bologna – Policlinico Sant’Orsola-Malpighi, Bologna, Italy  
Contact: taffache@gmail.com

## Funding and AI disclosure
Funding: **None**.

AI-assisted tools were used during software development, code review, documentation, and packaging. Scientific assumptions, source selection, validation decisions, and final responsibility remained with the author.

## License
MIT License. Copyright (c) 2026 Paolo Taffache.
