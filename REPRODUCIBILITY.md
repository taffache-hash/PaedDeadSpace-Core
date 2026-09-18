# Reproducibility

## Environment
Use Python 3.11, 3.12, or 3.13. Create a fresh virtual environment where practical.

## Core tests
```bash
python -m pip install -e .
python -m pip install "pytest>=8,<10"
python -m pytest -q tests
```
Expected result for v1.0.0: **47 passed**.

## Validation tests
```bash
python -m pip install -r requirements-validation.txt
PYTHONPATH=src:. python -m pytest -q validation_tests
```
Expected result for v1.0.0: **13 passed**.

## Golden Pearsall benchmark
Use 10 kg, 2 years, VT 8 mL/kg, RR 20/min, Pearsall patient VD/VT 0.30, apparatus DS 30 mL. Expected primary outputs are:

| Output | Expected |
|---|---:|
| VT | 80 mL |
| Patient VD | 24 mL |
| Apparatus VD | 30 mL |
| Total VD | 54 mL |
| Total VD/VT | 0.675 (67.5%) |
| Alveolar VT | 26 mL |
| Current alveolar ventilation | 520 mL/min |
| No-added-apparatus baseline | 1120 mL/min |
| Relative CO₂ burden | 2.154 |
| RR required | 43.08/min |
| RR multiplier | 2.154 |

This benchmark is for deterministic verification only and is not a physiological default or clinical target.
