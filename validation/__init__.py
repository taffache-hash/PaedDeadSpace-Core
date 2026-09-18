"""External validation and exploration for the audited PaedDeadSpace core.

This package is educational validation tooling, not clinical decision support.
The installed :mod:`paeddeadspace` package remains the scientific source of
truth.
"""

from .scenarios import generate_all_rows

__all__ = ["generate_all_rows"]
