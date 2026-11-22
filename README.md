# Supplementary Code: Spectrally Equivalent Window Workflow

This package provides a compact implementation of the spectrally equivalent (SE) workflow used in the manuscript:

**Revisiting solar admission through windows: natural spectral modeling**

The code converts wavelength-resolved solar spectra and wavelength-dependent glazing optical properties into time-dependent scalar inputs that can be used by standard EnergyPlus window objects. The examples cover three representative window types: static glazing, electrochromic glazing, and thermochromic glazing.

This package demonstrates the SE preprocessing step and EnergyPlus-compatible object generation. It is not a complete annual EnergyPlus simulation package. Full-year simulations can be generated with the same workflow by replacing the example one-day solar spectra with 8760 hourly spectra and inserting the generated IDF snippets into a complete EnergyPlus model.

## 1. Core calculation

For a glazing optical property `x(lambda)`, the SE coefficient at time `t` is calculated as:

```text
x_SE(t) = integral[E(lambda,t) x(lambda) dlambda] / integral[E(lambda,t) dlambda]
```

where:

- `E(lambda,t)` is the incident solar spectral irradiance;
- `x(lambda)` is a wavelength-dependent glazing optical property;
- `x_SE(t)` is the spectrum-weighted scalar property passed to EnergyPlus.

The code calculates the following properties:

- solar transmittance;
- front-side solar reflectance;
- back-side solar reflectance;
- visible transmittance;
- front-side visible reflectance;
- back-side visible reflectance;
- derived front-side and back-side solar absorptance.

Visible-range quantities are weighted using an embedded approximation of the CIE photopic luminous-efficiency function. Users who require strict color-science compliance can replace this function with a tabulated CIE function in `se_model/spectral_weighting.py`.

## 2. Package structure

```text
Supplementary_Code/
|-- README.md
|-- MANIFEST.txt
|-- requirements.txt
|-- run_all_examples.py
|
|-- data/
|   |-- solar_spectra_example.xlsx
|   `-- glazing_spectra_example.xlsx
|
|-- se_model/
|   |-- __init__.py
|   |-- spectral_weighting.py
|   |-- input_reader.py
|   `-- idf_writer.py
|
|-- examples/
|   |-- 01_static_window.py
|   |-- 02_electrochromic_window.py
|   `-- 03_thermochromic_window.py
|
`-- expected_output/
    |-- static_se_coefficients.csv
    |-- electrochromic_se_coefficients.csv
    |-- thermochromic_se_coefficients.csv
    |-- static_idf_snippet.idf
    |-- electrochromic_idf_snippet.idf
    `-- thermochromic_idf_snippet.idf
```

## 3. Input data

### 3.1 Solar spectra

The example file is:

```text
data/solar_spectra_example.xlsx
```

The first column must be `wavelength_nm`. Each subsequent column contains one incident solar spectrum in W m-2 nm-1. The example spectra correspond to daytime hours on 1 January in Beijing.

Example format:

```text
wavelength_nm | Beijing_Jan01_0800 | Beijing_Jan01_0900 | ...
300           | value               | value               | ...
305           | value               | value               | ...
```

The same format can be used for any site, orientation, or time sequence.

### 3.2 Glazing spectra

The example file is:

```text
data/glazing_spectra_example.xlsx
```

Each sheet represents one glazing family. The first column must be `wavelength_nm`. Optical columns should use the following naming pattern:

```text
<state>_transmittance
<state>_front_reflectance
<state>_back_reflectance
```

For a static glazing sheet, the state prefix can be omitted:

```text
wavelength_nm | transmittance | front_reflectance | back_reflectance
```

For an electrochromic glazing sheet:

```text
wavelength_nm | S1_transmittance | S1_front_reflectance | S1_back_reflectance | S2_transmittance | ...
```

For a thermochromic glazing sheet:

```text
wavelength_nm | 20_transmittance | 20_front_reflectance | 20_back_reflectance | 30_transmittance | ...
```

The sheet names used in the examples are `CW`, `EW2`, and `TW2`. These names are examples only. Users can replace them with other glazing systems by modifying the sheet names and state names in the example scripts.

## 4. Examples

### 4.1 Static glazing

```bash
python examples/01_static_window.py
```

This example calculates one SE coefficient set for each solar spectrum and writes:

```text
expected_output/static_se_coefficients.csv
expected_output/static_idf_snippet.idf
```

### 4.2 Electrochromic glazing

```bash
python examples/02_electrochromic_window.py
```

This example calculates SE coefficients for three optical states (`S1`, `S2`, `S3`). In the example control logic, `S1` represents clear/bleached, `S2` represents an intermediate state, and `S3` represents tinted/dark. The generated EMS skeleton uses an irradiance-based state selection:

```text
G_ctrl < 200 W m-2       -> S1
200 <= G_ctrl < 400 W m-2 -> S2
G_ctrl >= 400 W m-2      -> S3
```

The outputs are:

```text
expected_output/electrochromic_se_coefficients.csv
expected_output/electrochromic_idf_snippet.idf
```

### 4.3 Thermochromic glazing

```bash
python examples/03_thermochromic_window.py
```

This example calculates SE coefficients for five temperature states: 20, 30, 40, 50, and 60 degrees C. The generated IDF snippet includes `WindowMaterial:GlazingGroup:Thermochromic` objects. EMS only selects the hour-specific construction; the thermochromic optical state is selected by EnergyPlus through its native temperature-dependent glazing algorithm.

The outputs are:

```text
expected_output/thermochromic_se_coefficients.csv
expected_output/thermochromic_idf_snippet.idf
```

## 5. Run all examples

From the package root:

```bash
python run_all_examples.py
```

The command regenerates all CSV and IDF snippet files in `expected_output/`.

## 6. Output files

### 6.1 SE coefficient files

The CSV files contain one row per time step and, where applicable, per optical state or temperature state. Main columns include:

```text
time_index
spectrum_label
state
solar_transmittance
front_solar_reflectance
back_solar_reflectance
front_solar_absorptance
back_solar_absorptance
visible_transmittance
front_visible_reflectance
back_visible_reflectance
```

### 6.2 IDF snippet files

The generated IDF snippets contain EnergyPlus-compatible objects:

- `WindowMaterial:Glazing`
- `Construction`
- `WindowMaterial:GlazingGroup:Thermochromic` for thermochromic glazing
- EMS actuator and program skeletons for construction switching

The snippets use the placeholder surface name `REPLACE_WITH_WINDOW_SURFACE_NAME`. Before insertion into a complete EnergyPlus model, this placeholder should be replaced with the actual `FenestrationSurface:Detailed` name of the target window surface. Control sensors can also be adapted to the target model, orientation, and control strategy.

Full building IDF files are not included in this package. The aim is to provide a compact and reproducible implementation of the SE preprocessing workflow and EnergyPlus-compatible object generation, rather than a full building simulation case.

## 7. Software environment

The examples require Python 3.9 or later and the packages listed in `requirements.txt`:

```text
numpy
pandas
openpyxl
```

Install dependencies with:

```bash
pip install -r requirements.txt
```

EnergyPlus is not required to run the example scripts. The generated IDF snippets are compatible with standard EnergyPlus window objects and can be inserted into complete EnergyPlus models for simulation.

## 8. License and reuse

This package is provided for reviewer assessment and reproducibility of the SE workflow. Users may adapt the scripts to their own solar spectra, glazing spectra, and EnergyPlus models.
