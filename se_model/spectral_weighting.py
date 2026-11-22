"""
Spectrally equivalent (SE) optical-property calculations.

The central operation is

    x_SE(t) = integral[E(lambda,t) x(lambda) dlambda] / integral[E(lambda,t) dlambda]

where E(lambda,t) is the incident solar spectral irradiance and x(lambda)
is a wavelength-dependent glazing optical property.

This module is intentionally independent of EnergyPlus. It converts measured
or modeled spectra and glazing spectra into scalar coefficients that can be
written to EnergyPlus glazing objects.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SolarSpectra:
    """Solar spectral irradiance dataset.

    Attributes
    ----------
    wavelength_nm:
        One-dimensional wavelength grid in nm.
    irradiance:
        DataFrame indexed by wavelength, with one column per time step.
        Values are spectral irradiance in W m^-2 nm^-1.
    """

    wavelength_nm: np.ndarray
    irradiance: pd.DataFrame


@dataclass(frozen=True)
class GlazingState:
    """Wavelength-dependent glazing optical properties for one state."""

    wavelength_nm: np.ndarray
    transmittance: np.ndarray
    front_reflectance: np.ndarray
    back_reflectance: np.ndarray


def _as_float_array(values: Iterable[float], name: str) -> np.ndarray:
    arr = np.asarray(list(values), dtype=float)
    if arr.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional.")
    if not np.isfinite(arr).all():
        raise ValueError(f"{name} contains NaN or infinite values.")
    return arr


def interpolate_to_grid(source_wavelength_nm: np.ndarray,
                        source_values: np.ndarray,
                        target_wavelength_nm: np.ndarray) -> np.ndarray:
    """Interpolate spectral values onto a target wavelength grid.

    Values outside the source wavelength range are set to zero. This is safer
    than extrapolation for spectral integration.
    """
    source_wavelength_nm = _as_float_array(source_wavelength_nm, "source_wavelength_nm")
    source_values = _as_float_array(source_values, "source_values")
    target_wavelength_nm = _as_float_array(target_wavelength_nm, "target_wavelength_nm")

    order = np.argsort(source_wavelength_nm)
    x = source_wavelength_nm[order]
    y = source_values[order]
    return np.interp(target_wavelength_nm, x, y, left=0.0, right=0.0)


def integrate_trapezoid(wavelength_nm: np.ndarray, values: np.ndarray) -> float:
    """Integrate values over wavelength using the trapezoidal rule."""
    wavelength_nm = _as_float_array(wavelength_nm, "wavelength_nm")
    values = _as_float_array(values, "values")
    if len(wavelength_nm) != len(values):
        raise ValueError("wavelength_nm and values must have the same length.")
    return float(np.trapz(values, wavelength_nm))


def photopic_v_lambda(wavelength_nm: np.ndarray) -> np.ndarray:
    """Approximate CIE 1924 photopic luminous-efficiency function V(lambda).

    A compact analytic approximation is used so that the example code has no
    external dependency on a colour-science package. For publication-grade
    photometry, users may replace this function with a tabulated CIE V(lambda).
    """
    wl = np.asarray(wavelength_nm, dtype=float)
    t = (wl - 556.3) * np.where(wl < 556.3, 0.0213, 0.0247)
    v = 1.014 * np.exp(-0.5 * t * t)
    v[(wl < 380.0) | (wl > 780.0)] = 0.0
    return v


def weighted_average(wavelength_nm: np.ndarray,
                     incident_spectrum: np.ndarray,
                     optical_property: np.ndarray,
                     weighting_function: Optional[np.ndarray] = None) -> float:
    """Return the spectrum-weighted average optical property.

    Parameters
    ----------
    wavelength_nm:
        Wavelength grid in nm.
    incident_spectrum:
        Incident spectral irradiance on that grid.
    optical_property:
        Optical property on that grid, e.g. transmittance or reflectance.
    weighting_function:
        Optional additional weighting. Use the photopic response for visible
        properties. If omitted, broadband radiometric weighting is used.
    """
    wavelength_nm = _as_float_array(wavelength_nm, "wavelength_nm")
    E = _as_float_array(incident_spectrum, "incident_spectrum")
    x = _as_float_array(optical_property, "optical_property")
    if len(wavelength_nm) != len(E) or len(wavelength_nm) != len(x):
        raise ValueError("wavelength_nm, incident_spectrum and optical_property must have equal length.")

    if weighting_function is None:
        w = np.ones_like(E)
    else:
        w = _as_float_array(weighting_function, "weighting_function")
        if len(w) != len(E):
            raise ValueError("weighting_function must have the same length as incident_spectrum.")

    denominator = integrate_trapezoid(wavelength_nm, E * w)
    if abs(denominator) < 1e-15:
        return float("nan")
    numerator = integrate_trapezoid(wavelength_nm, E * w * x)
    return float(numerator / denominator)


def calculate_state_coefficients(solar: SolarSpectra,
                                 glazing_state: GlazingState,
                                 wavelength_min_nm: float = 300.0,
                                 wavelength_max_nm: float = 2500.0) -> pd.DataFrame:
    """Calculate SE coefficients for one glazing state across all time steps.

    Returns a DataFrame with one row per time step and columns:
    solar_transmittance, front_solar_reflectance, back_solar_reflectance,
    visible_transmittance, front_visible_reflectance, back_visible_reflectance.
    """
    wl_solar = np.asarray(solar.wavelength_nm, dtype=float)
    mask = (wl_solar >= wavelength_min_nm) & (wl_solar <= wavelength_max_nm)
    wl = wl_solar[mask]

    tau = interpolate_to_grid(glazing_state.wavelength_nm, glazing_state.transmittance, wl)
    rf = interpolate_to_grid(glazing_state.wavelength_nm, glazing_state.front_reflectance, wl)
    rb = interpolate_to_grid(glazing_state.wavelength_nm, glazing_state.back_reflectance, wl)
    photopic = photopic_v_lambda(wl)

    rows = []
    for time_label in solar.irradiance.columns:
        E = solar.irradiance.loc[wl_solar[mask], time_label].to_numpy(dtype=float)
        row = {
            "time": str(time_label),
            "solar_transmittance": weighted_average(wl, E, tau),
            "front_solar_reflectance": weighted_average(wl, E, rf),
            "back_solar_reflectance": weighted_average(wl, E, rb),
            "visible_transmittance": weighted_average(wl, E, tau, photopic),
            "front_visible_reflectance": weighted_average(wl, E, rf, photopic),
            "back_visible_reflectance": weighted_average(wl, E, rb, photopic),
        }
        # Absorptance is reported for checking but is not written directly to
        # WindowMaterial:Glazing in the simple IDF writer.
        row["front_solar_absorptance"] = 1.0 - row["solar_transmittance"] - row["front_solar_reflectance"]
        row["back_solar_absorptance"] = 1.0 - row["solar_transmittance"] - row["back_solar_reflectance"]
        rows.append(row)

    return pd.DataFrame(rows)


def calculate_all_states(solar: SolarSpectra,
                         glazing_states: Mapping[str, GlazingState]) -> Dict[str, pd.DataFrame]:
    """Calculate SE coefficients for multiple glazing states."""
    return {state_name: calculate_state_coefficients(solar, state)
            for state_name, state in glazing_states.items()}


def combine_state_tables(state_tables: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    """Combine per-state coefficient tables into one long-form DataFrame."""
    frames = []
    for state_name, df in state_tables.items():
        tmp = df.copy()
        tmp.insert(1, "state", state_name)
        frames.append(tmp)
    if not frames:
        raise ValueError("No state tables were supplied.")
    return pd.concat(frames, ignore_index=True)
