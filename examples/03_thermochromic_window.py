"""Thermochromic-window SE workflow example."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from se_model.input_reader import read_glazing_spectra, read_solar_spectra
from se_model.spectral_weighting import calculate_all_states, combine_state_tables
from se_model.idf_writer import write_thermochromic_snippet


def main(output_dir: str | Path = ROOT / "expected_output") -> None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    solar = read_solar_spectra(ROOT / "data" / "solar_spectra_example.xlsx")
    temperatures_c = [20, 30, 40, 50, 60]
    state_names = [str(t) for t in temperatures_c]
    glazing_states = read_glazing_spectra(
        ROOT / "data" / "glazing_spectra_example.xlsx",
        sheet_name="TW2",
        state_names=state_names,
    )

    state_tables = calculate_all_states(solar, glazing_states)
    long_coeffs = combine_state_tables(state_tables)
    long_coeffs.to_csv(output_dir / "thermochromic_se_coefficients.csv", index=False)

    surfaces = ["REPLACE_WITH_WINDOW_SURFACE_NAME"]
    snippet = write_thermochromic_snippet(
        long_coeffs,
        temperature_states_c=temperatures_c,
        prefix="SE_TC",
        surface_names=surfaces,
    )
    (output_dir / "thermochromic_idf_snippet.idf").write_text(snippet, encoding="utf-8")

    print(f"Thermochromic-window example complete: {len(long_coeffs)} time-state rows. IDF snippet uses placeholder surface names.")


if __name__ == "__main__":
    main()
