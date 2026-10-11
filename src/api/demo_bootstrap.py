"""Prepare synthetic data for the public portfolio demo."""

from pathlib import Path
import shutil


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def prepare_demo_data():
    """Populate expected local paths from versioned demo data."""
    demo_root = PROJECT_ROOT / "data" / "demo"
    raw_root = PROJECT_ROOT / "data" / "raw"

    for folder in ("sap", "documents"):
        source = demo_root / folder
        destination = raw_root / folder

        if destination.exists():
            continue

        if not source.is_dir():
            raise FileNotFoundError(
                f"Demo dataset missing: {source}"
            )

        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, destination)
