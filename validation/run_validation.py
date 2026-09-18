"""Command-line entry point for deterministic validation output generation."""

from __future__ import annotations

from pathlib import Path

from .reporting import write_validation_outputs
from .scenarios import generate_all_rows


def run(output_dir: str | Path = "outputs") -> list[Path]:
    """Generate CSV, markdown, and PNG files and return their paths."""
    rows = generate_all_rows()
    return write_validation_outputs(rows, Path(output_dir))


def main() -> None:
    paths = run()
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
