"""
Input readers for the SE workflow examples.

The readers are deliberately permissive. They support the example Excel files
provided with this code package and similar user-prepared files with the same
logic:

- solar spectra: first column = wavelength, remaining columns = spectra at
  different times;
- glazing spectra: first column = wavelength, then columns for transmittance,
  front reflectance and back reflectance, either for a single state or for
  multiple states.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from .spectral_weighting import GlazingState, SolarSpectra


def _clean_header(value) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    text = text.replace(" ", "")
    text = text.replace("_", "")
    text = text.lower()
    return text


def _read_excel_first_nonempty_sheet(path: Path) -> pd.DataFrame:
    sheets = pd.read_excel(path, sheet_name=None, header=None)
    for _, df in sheets.items():
        if df.dropna(how="all").shape[0] > 1 and df.dropna(axis=1, how="all").shape[1] > 1:
            return df
    raise ValueError(f"No non-empty data sheet was found in {path}.")


def read_solar_spectra(path: str | Path, sheet_name: Optional[str] = None) -> SolarSpectra:
    """Read solar spectra from Excel or CSV.

    The example solar file has time labels on row 1, units on row 2, wavelength
    in column 1, and spectral irradiance values in columns 2..N. This function
    also supports simpler files with one header row.
    """
    path = Path(path)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        if sheet_name is None:
            raw = _read_excel_first_nonempty_sheet(path)
        else:
            raw = pd.read_excel(path, sheet_name=sheet_name, header=None)
    else:
        raw = pd.read_csv(path, header=None)

    raw = raw.dropna(axis=0, how="all").dropna(axis=1, how="all").reset_index(drop=True)

    # Detect the first row in which the first cell is numeric. That is the start
    # of the spectral table.
    data_start = None
    for i in range(len(raw)):
        try:
            float(raw.iloc[i, 0])
            data_start = i
            break
        except Exception:
            continue
    if data_start is None:
        raise ValueError("Could not find numeric wavelength rows in solar spectra file.")

    if data_start == 0:
        time_labels = [f"t{j:03d}" for j in range(1, raw.shape[1])]
    else:
        candidate_labels = list(raw.iloc[0, 1:])
        time_labels = []
        for j, label in enumerate(candidate_labels, start=1):
            if pd.isna(label):
                time_labels.append(f"t{j:03d}")
            else:
                time_labels.append(str(label))

    data = raw.iloc[data_start:, :].copy()
    wavelength = pd.to_numeric(data.iloc[:, 0], errors="coerce")
    valid = wavelength.notna()
    data = data.loc[valid, :]
    wavelength = wavelength.loc[valid].astype(float).to_numpy()

    spectra = {}
    for col_idx in range(1, data.shape[1]):
        values = pd.to_numeric(data.iloc[:, col_idx], errors="coerce").fillna(0.0).astype(float).to_numpy()
        label = time_labels[col_idx - 1] if col_idx - 1 < len(time_labels) else f"t{col_idx:03d}"
        spectra[label] = values

    df = pd.DataFrame(spectra, index=wavelength)
    df.index.name = "wavelength_nm"
    return SolarSpectra(wavelength_nm=wavelength, irradiance=df)


def _property_kind(header: str) -> Optional[str]:
    h = _clean_header(header)
    if any(token in h for token in ["transmittance", "transmission", "tau"]):
        return "transmittance"
    if any(token in h for token in ["frontreflectance", "frontreflection", "rho_f", "rhof", "front"]):
        return "front_reflectance"
    if any(token in h for token in ["backreflectance", "backreflection", "rho_b", "rhob", "back"]):
        return "back_reflectance"
    if any(token in h for token in ["reflectance", "reflection", "rho"]):
        # If only one reflectance column is supplied, use it for both sides.
        return "reflectance"
    return None


def _state_prefix(header: str, kind: Optional[str]) -> str:
    text = str(header).strip()
    if kind == "transmittance":
        patterns = ["transmittance", "transmission", "tau"]
    elif kind == "front_reflectance":
        patterns = ["front_reflectance", "front reflectance", "frontreflectance", "front_reflection", "front reflection", "frontreflection",
                    "rho_f", "rhof", "front"]
    elif kind == "back_reflectance":
        patterns = ["back_reflectance", "back reflectance", "backreflectance", "back_reflection", "back reflection", "backreflection",
                    "rho_b", "rhob", "back"]
    elif kind == "reflectance":
        patterns = ["reflectance", "reflection", "rho"]
    else:
        patterns = []

    prefix = text
    for pat in patterns:
        prefix = re.sub(re.escape(pat), "", prefix, flags=re.IGNORECASE)
    prefix = prefix.strip(" _-:")
    if prefix == "":
        prefix = "default"
    return prefix


def read_glazing_spectra(path: str | Path,
                         sheet_name: str,
                         state_names: Optional[Sequence[str]] = None) -> Dict[str, GlazingState]:
    """Read glazing spectra for one sheet.

    The sheet must have wavelength in the first column. The remaining columns
    should contain transmittance, front reflectance and back reflectance. For a
    stateful glazing, columns should be grouped by state, such as S1 transmittance,
    S1 front reflectance, S1 back reflectance, S2 ...
    """
    path = Path(path)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(path, sheet_name=sheet_name)
    else:
        df = pd.read_csv(path)

    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
    if df.shape[1] < 4:
        raise ValueError(f"Glazing sheet {sheet_name} must contain wavelength + at least three property columns.")

    wavelength = pd.to_numeric(df.iloc[:, 0], errors="coerce")
    valid = wavelength.notna()
    df = df.loc[valid, :].reset_index(drop=True)
    wavelength = pd.to_numeric(df.iloc[:, 0], errors="coerce").astype(float).to_numpy()

    grouped: Dict[str, Dict[str, np.ndarray]] = {}
    for col in df.columns[1:]:
        kind = _property_kind(str(col))
        if kind is None:
            continue
        state = _state_prefix(str(col), kind)
        # Normalize common state names.
        state_clean = state.strip()
        if state_clean.lower().startswith("s"):
            state_clean = state_clean.upper()
        grouped.setdefault(state_clean, {})
        values = pd.to_numeric(df[col], errors="coerce").interpolate(limit_direction="both").fillna(0.0)
        grouped[state_clean][kind] = values.astype(float).to_numpy()

    if not grouped:
        raise ValueError(f"No optical-property columns were detected in sheet {sheet_name}.")

    # If the sheet was static, the state name may be "default".
    if state_names is not None:
        # Keep state names supplied by the user/config, matching case-insensitively.
        remapped = {}
        for requested in state_names:
            found = None
            for existing in grouped:
                if existing.lower() == requested.lower():
                    found = existing
                    break
            if found is None:
                raise ValueError(f"State {requested} was not found in sheet {sheet_name}. Available: {list(grouped)}")
            remapped[requested] = grouped[found]
        grouped = remapped

    states: Dict[str, GlazingState] = {}
    for state, props in grouped.items():
        if "reflectance" in props:
            props.setdefault("front_reflectance", props["reflectance"])
            props.setdefault("back_reflectance", props["reflectance"])
        missing = [k for k in ["transmittance", "front_reflectance", "back_reflectance"] if k not in props]
        if missing:
            raise ValueError(f"State {state} in sheet {sheet_name} is missing {missing}.")
        states[state] = GlazingState(
            wavelength_nm=wavelength,
            transmittance=props["transmittance"],
            front_reflectance=props["front_reflectance"],
            back_reflectance=props["back_reflectance"],
        )

    return states
