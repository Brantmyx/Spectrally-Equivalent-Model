# Spectrally-Equivalent-Model

## Introduction

Spectrally-Equivalent-Model is a Python-based tool developed to incorporate time-varying solar spectra into the performance evaluation of spectrally selective windows (SSWs). Conventional building energy simulations typically use glazing optical properties weighted by a fixed reference solar spectrum (AM1.5G), whereas the spectral composition of sunlight varies with atmospheric conditions, location, and time.

The spectrally equivalent (SE) model addresses this mismatch by combining incident solar spectral irradiance with the wavelength-dependent optical properties of glazing. It calculates time-dependent equivalent transmittance, reflectance, and absorptance, which can be incorporated into EnergyPlus through glazing construction definitions and Energy Management System (EMS) controls without modifying the underlying simulation solver.

The main functions of this tool include:

1. **Spectral weighting:** Calculate equivalent solar and visible optical properties using time-varying incident solar spectra and wavelength-dependent glazing properties.
2. **Glazing input generation:** Convert the calculated optical properties into glazing material and construction definitions for EnergyPlus.
3. **Dynamic window implementation:** Generate time-dependent glazing inputs for static, electrochromic, and thermochromic window systems.

Three examples are provided to demonstrate the SE workflow:

1. **Static window (Example 01):** Calculate SE optical properties for a clear window (CW) under different incident solar spectra.
2. **Electrochromic window (Example 02):** Calculate SE optical properties for an electrochromic window (EW2) with three optical states.
3. **Thermochromic window (Example 03):** Calculate SE optical properties for a thermochromic window (TW2) with five temperature-dependent states.

The examples illustrate the core SE calculations and the generation of optical inputs for EnergyPlus. Users can apply the same spectral-weighting workflow to other glazing systems and solar spectral datasets.

Technical details of the SE model, including its experimental validation and building-scale applications, are presented in our paper, *Revisiting solar admission through windows: natural spectral modeling* (Ma et al.). Please cite the corresponding publication when using this tool in research.

## System Requirements

### Software Dependencies

- Python 3.10 or higher
- NumPy
- pandas
- openpyxl

The required Python packages are listed in `requirements.txt`.

EnergyPlus is used for whole-building simulation applications. The Python examples can be executed independently to generate SE optical coefficients and EnergyPlus input files.

### Required Non-Standard Hardware

No non-standard hardware is required.

## Installation and Demo

**Step 1. Download the code**

Click **Code → Download ZIP** on the GitHub repository page and extract the downloaded files to your computer.

Alternatively, clone the repository using Git.

**Step 2. Install the required packages**

Open a terminal in the repository directory and run:

`pip install -r requirements.txt`

**Step 3. Run the examples**

To execute all three examples, run:

`python run_all_examples.py`

Alternatively, run each example separately:

- **Example 01 — Static window:** `python examples/01_static_window.py`
- **Example 02 — Electrochromic window:** `python examples/02_electrochromic_window.py`
- **Example 03 — Thermochromic window:** `python examples/03_thermochromic_window.py`

**Step 4. Input data**

The example input files are provided in the `data` folder:

- `solar_spectra_example.xlsx`: Incident solar spectral irradiance for nine daytime hours in Beijing.
- `glazing_spectra_example.xlsx`: Wavelength-dependent transmittance and front- and back-side reflectance for CW, EW2, and TW2.

Users can replace the example spectra with their own solar and glazing optical data using the same input formats.

**Step 5. Expected output**

The calculated results are saved in the `expected_output` folder:

- **SE coefficient files (.csv):** Time-dependent solar and visible optical properties for the selected glazing systems.
- **EnergyPlus input files (.idf):** Glazing material, construction, and EMS control definitions generated from the SE coefficients.

The three examples produce:

- **Static window:** 9 time-dependent SE coefficient sets.
- **Electrochromic window:** 27 time–state combinations (9 hours × 3 states).
- **Thermochromic window:** 45 time–temperature combinations (9 hours × 5 states).

The generated optical coefficients can be used to prepare glazing inputs for building simulations under varying incident solar spectra.

## License

See the `LICENSE` file for details.
