"""Streamlit Community Cloud entrypoint."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

exec(
    compile(
        (ROOT / "app.py").read_text(encoding="utf-8"),
        str(ROOT / "app.py"),
        "exec",
    ),
    {"__name__": "__main__", "__file__": str(ROOT / "app.py")},
)
