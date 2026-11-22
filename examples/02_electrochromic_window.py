"""Electrochromic-window SE workflow example."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from se_model.input_reader import read_glazing_spectra, read_solar_spectra
from se_model.spectral_weighting import calculate_all_states, combine_state_tables
from se_model.idf_writer import write_electrochromic_snippet


def main(output_dir: str | Path = ROOT / "expected_output") -> None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    solar = read_solar_spectra(ROOT / "data" / "solar_spectra_example.xlsx")
    states = ["S1", "S2", "S3"]  # S1=clear/bleached, S2=intermediate, S3=tinted/dark in this example.
    glazing_states = read_glazing_spectra(
        ROOT / "data" / "glazing_spectra_example.xlsx",
        sheet_name="EW2",
        state_names=states,
    )

    state_tables = calculate_all_states(solar, glazing_states)
    long_coeffs = combine_state_tables(state_tables)
    long_coeffs.to_csv(output_dir / "electrochromic_se_coefficients.csv", index=False)

    surfaces = ["REPLACE_WITH_WINDOW_SURFACE_NAME"]
    snippet = write_electrochromic_snippet(
        long_coeffs,
        states=states,
        prefix="SE_EC",
        surface_names=surfaces,
        irradiance_thresholds_w_m2=(200.0, 400.0),
    )
    (output_dir / "electrochromic_idf_snippet.idf").write_text(snippet, encoding="utf-8")

    print(f"Electrochromic-window example complete: {len(long_coeffs)} time-state rows. IDF snippet uses placeholder surface names.")


if __name__ == "__main__":
    main()
