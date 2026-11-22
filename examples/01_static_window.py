"""Static-window SE workflow example."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from se_model.input_reader import read_glazing_spectra, read_solar_spectra
from se_model.spectral_weighting import calculate_all_states, combine_state_tables
from se_model.idf_writer import write_static_snippet


def main(output_dir: str | Path = ROOT / "expected_output") -> None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    solar = read_solar_spectra(ROOT / "data" / "solar_spectra_example.xlsx")
    glazing_states = read_glazing_spectra(ROOT / "data" / "glazing_spectra_example.xlsx", sheet_name="CW")
    state_name = next(iter(glazing_states.keys()))

    coeffs = calculate_all_states(solar, glazing_states)[state_name]
    coeffs.to_csv(output_dir / "static_se_coefficients.csv", index=False)

    surfaces = ["REPLACE_WITH_WINDOW_SURFACE_NAME"]
    snippet = write_static_snippet(coeffs, prefix="SE_Static", surface_names=surfaces)
    (output_dir / "static_idf_snippet.idf").write_text(snippet, encoding="utf-8")

    print(f"Static-window example complete: {len(coeffs)} time steps. IDF snippet uses placeholder surface names.")


if __name__ == "__main__":
    main()
