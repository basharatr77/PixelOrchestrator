import subprocess
import sys


def test_main_runtime_boundary():
    code = r"""
import sys
import main

loaded = [
    m for m in sys.modules
    if m.startswith(("app.core.", "architecture."))
]

if loaded:
    print("\nUnexpected modules:")
    for module in sorted(loaded):
        print(module)
    raise SystemExit(1)
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, (
        "main.py crossed the runtime boundary.\n"
        + result.stdout
        + result.stderr
    )
