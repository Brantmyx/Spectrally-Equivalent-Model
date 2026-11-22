# Spectrally-Equivalent-Model

## Introduction

Spectrally-Equivalent-Model is a Python tool for calculating the optical properties of glazing under time-varying solar spectra. Spectrally selective windows respond differently to different wavelengths of sunlight, whereas conventional building simulations commonly use glazing properties weighted by a fixed reference spectrum (AM1.5G). The spectrally equivalent (SE) approach combines the incident solar spectral irradiance with wavelength-dependent glazing properties to obtain time-dependent optical inputs for building simulation.

For an optical property of glazing, the SE calculation is

\[
x_{\mathrm{SE}}(t)=\frac{\int_{\lambda_1}^{\lambda_2} E(\lambda,t)x(\lambda)\,\mathrm{d}\lambda}{\int_{\lambda_1}^{\lambda_2} E(\lambda,t)\,\mathrm{d}\lambda}.
\]

where \(E(\lambda,t)\) is the incident solar spectral irradiance and \(x(\lambda)\) is the spectral optical property of the glazing. The code calculates spectrum-weighted transmittance and front- and back-side reflectance, with absorptance derived from energy conservation. These results can be used to prepare time-dependent glazing definitions for EnergyPlus without changing its underlying simulation solvers.

The repository provides three examples:

1. **Static window (Example 01):** Calculate SE optical properties for clear glazing (CW) under successive solar spectra.
2. **Electrochromic window (Example 02):** Calculate SE optical properties for three states of an electrochromic window (EW2).
3. **Thermochromic window (Example 03):** Calculate SE optical properties for five temperature-dependent states of a thermochromic window (TW2).

The example programs illustrate spectral preprocessing and generation of glazing input files. They are not a complete annual building-simulation package.

The method is described in the manuscript *Revisiting solar admission through windows: natural spectral modeling* (Ma et al., Nature Communications, pending publication). Please cite the published article when using this tool in research.

## System Requirements

### Software Dependencies

- Python 3.9 or later
- NumPy, pandas and openpyxl (see `requirements.txt`)
- EnergyPlus is not required to run the Python examples. A complete EnergyPlus model is needed for building simulations.

### Operating Systems

The examples use standard Python libraries. Operating-system compatibility has not been systematically verified.

### Tested Versions

- Python 3.13.5: the three example scripts were executed successfully; the generated CSV and IDF files matched the supplied example outputs.
- EnergyPlus integration and the generated EMS/IDF snippets have not been validated in a complete building model. The current EMS construction-switching definitions require correction and testing before use in simulations.

### Required Non-Standard Hardware

No non-standard hardware is required for the Python examples.

## Installation and Demo

1. Download the repository using **Code → Download ZIP** on GitHub and extract it to your computer, or clone the repository.

2. Open a terminal in the repository folder and install the dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Run all three examples:

   ```bash
   python run_all_examples.py
   ```

   Alternatively, run one example:

   ```bash
   python examples/01_static_window.py
   python examples/02_electrochromic_window.py
   python examples/03_thermochromic_window.py
   ```

4. Check the results in `expected_output/`. Each example writes SE optical coefficients (`.csv`) and illustrative EnergyPlus input snippets (`.idf`). Running the examples regenerates these files.

The example solar spectra are in `data/solar_spectra_example.xlsx`, and the glazing spectra are in `data/glazing_spectra_example.xlsx`. The solar file contains nine daytime spectra; the glazing file contains the corresponding example CW, EW2 and TW2 spectral properties. Users can replace these inputs with their own spectra following the formats described in the accompanying Supplementary Code documentation.

**Expected output:** SE coefficients for nine time steps in Example 01, 27 time–state combinations in Example 02 and 45 time–state combinations in Example 03. The IDF files are illustrative inputs, not ready-to-run or validated EnergyPlus building models. The visible-light weighting function in this demonstration uses an approximation of the CIE photopic response and should not be treated as a full reproduction of the article's colorimetric calculations.

## License

See the repository's `LICENSE` file for the applicable terms once the license has been confirmed and added. The original Supplementary Code archive does not contain a complete license text; this must be resolved before public release.
