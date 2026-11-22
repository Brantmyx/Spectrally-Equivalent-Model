"""Run all SE workflow examples and regenerate the expected output files."""

from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "expected_output"
OUTPUT.mkdir(exist_ok=True)

for script in [
    ROOT / "examples" / "01_static_window.py",
    ROOT / "examples" / "02_electrochromic_window.py",
    ROOT / "examples" / "03_thermochromic_window.py",
]:
    print(f"\nRunning {script.name} ...")
    ns = runpy.run_path(str(script))
    ns["main"](OUTPUT)

print("\nAll examples completed. Outputs were written to:")
print(OUTPUT)
