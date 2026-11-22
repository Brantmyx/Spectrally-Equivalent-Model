"""
EnergyPlus IDF snippet writers for SE glazing examples.

The writers create ordinary EnergyPlus objects:

- WindowMaterial:Glazing
- Construction
- WindowMaterial:GlazingGroup:Thermochromic
- optional EMS skeletons for construction switching

The generated snippets are intentionally modular. They can be reviewed directly
or inserted into a complete EnergyPlus IDF after replacing placeholder surface names
and control sensors with project-specific names.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import pandas as pd


DEFAULT_GLAZING_PARAMETERS = {
    "thickness_m": 0.006,
    "infrared_transmittance": 0.0,
    "front_infrared_hemispherical_emissivity": 0.84,
    "back_infrared_hemispherical_emissivity": 0.84,
    "conductivity_w_mk": 1.0,
    "dirt_correction_factor": 1.0,
    "solar_diffusing": "No",
}


def _fmt(value, precision: int = 6) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    try:
        return f"{float(value):.{precision}f}".rstrip("0").rstrip(".")
    except Exception:
        return str(value)


def window_material_glazing(name: str,
                            coeffs: Mapping[str, float],
                            defaults: Optional[Mapping[str, float | str]] = None) -> str:
    """Return a WindowMaterial:Glazing object."""
    d = dict(DEFAULT_GLAZING_PARAMETERS)
    if defaults:
        d.update(defaults)

    return f"""WindowMaterial:Glazing,
    {name},                         !- Name
    SpectralAverage,                !- Optical Data Type
    ,                               !- Window Glass Spectral Data Set Name
    {_fmt(d['thickness_m'])},        !- Thickness {{m}}
    {_fmt(coeffs['solar_transmittance'])},        !- Solar Transmittance at Normal Incidence
    {_fmt(coeffs['front_solar_reflectance'])},    !- Front Side Solar Reflectance at Normal Incidence
    {_fmt(coeffs['back_solar_reflectance'])},     !- Back Side Solar Reflectance at Normal Incidence
    {_fmt(coeffs['visible_transmittance'])},      !- Visible Transmittance at Normal Incidence
    {_fmt(coeffs['front_visible_reflectance'])},  !- Front Side Visible Reflectance at Normal Incidence
    {_fmt(coeffs['back_visible_reflectance'])},   !- Back Side Visible Reflectance at Normal Incidence
    {_fmt(d['infrared_transmittance'])},          !- Infrared Transmittance at Normal Incidence
    {_fmt(d['front_infrared_hemispherical_emissivity'])},  !- Front Side Infrared Hemispherical Emissivity
    {_fmt(d['back_infrared_hemispherical_emissivity'])},   !- Back Side Infrared Hemispherical Emissivity
    {_fmt(d['conductivity_w_mk'])},               !- Conductivity {{W/m-K}}
    {_fmt(d['dirt_correction_factor'])},          !- Dirt Correction Factor for Solar and Visible Transmittance
    {d['solar_diffusing']};                       !- Solar Diffusing
"""


def construction(name: str, material_name: str) -> str:
    """Return a single-layer Construction object."""
    return f"""Construction,
    {name},                         !- Name
    {material_name};                !- Outside Layer
"""


def thermochromic_group(name: str, temp_material_pairs: Sequence[Tuple[float, str]]) -> str:
    """Return a WindowMaterial:GlazingGroup:Thermochromic object."""
    if not temp_material_pairs:
        raise ValueError("temp_material_pairs cannot be empty.")
    lines = ["WindowMaterial:GlazingGroup:Thermochromic,", f"    {name},                         !- Name"]
    for idx, (temperature_c, material_name) in enumerate(temp_material_pairs):
        end = ";" if idx == len(temp_material_pairs) - 1 else ","
        lines.append(f"    {_fmt(temperature_c)}, {material_name}{end}       !- Optical Data Temperature {{C}}, Window Material Glazing Name")
    return "\n".join(lines) + "\n"


def _ems_actuators(surface_names: Sequence[str]) -> str:
    blocks = []
    for surface in surface_names:
        safe = "".join(ch if ch.isalnum() else "_" for ch in surface)[:60]
        blocks.append(f"""EnergyManagementSystem:Actuator,
    SE_Construction_Actuator_{safe},  !- Name
    {surface},                        !- Actuated Component Unique Name
    Surface,                          !- Actuated Component Type
    Construction State;               !- Actuated Component Control Type
""")
    return "\n".join(blocks)


def _set_all_surfaces(surface_names: Sequence[str], construction_name: str) -> str:
    lines = []
    for surface in surface_names:
        safe = "".join(ch if ch.isalnum() else "_" for ch in surface)[:60]
        lines.append(f"        SET SE_Construction_Actuator_{safe} = {construction_name}")
    return "\n".join(lines)


def ems_static_switcher(construction_names: Sequence[str],
                        time_labels: Sequence[str],
                        surface_names: Sequence[str]) -> str:
    """Return an EMS skeleton for hourly construction switching."""
    conditions = []
    for idx, con in enumerate(construction_names, start=1):
        # The example spectra contain daytime hours only. The EMS skeleton maps
        # the first spectrum to Hour=8, the next to Hour=9, etc.
        hour = 7 + idx
        keyword = "IF" if idx == 1 else "ELSEIF"
        conditions.append(f"    {keyword} (Hour == {hour})")
        conditions.append(_set_all_surfaces(surface_names, con))
    conditions.append("    ELSE")
    conditions.append(_set_all_surfaces(surface_names, construction_names[0]))
    conditions.append("    ENDIF")

    return f"""!- EMS skeleton for static hourly SE construction switching.
{_ems_actuators(surface_names)}
EnergyManagementSystem:ProgramCallingManager,
    SE_Static_Window_Manager,         !- Name
    BeginTimestepBeforePredictor,     !- EnergyPlus Model Calling Point
    SE_Static_Window_Switcher;        !- Program Name

EnergyManagementSystem:Program,
    SE_Static_Window_Switcher,
{chr(10).join(conditions)};
"""


def ems_electrochromic_switcher(construction_by_time_state: Mapping[Tuple[int, str], str],
                                states: Sequence[str],
                                time_labels: Sequence[str],
                                surface_names: Sequence[str],
                                irradiance_thresholds_w_m2: Tuple[float, float] = (200.0, 400.0)) -> str:
    """Return an EMS skeleton for EC hourly and irradiance-based switching.

    The example uses S1=clear/bleached, S2=intermediate, S3=tinted/dark.
    """
    t_low, t_high = irradiance_thresholds_w_m2
    blocks = [
        "!- EMS skeleton for electrochromic hourly SE construction switching.",
        "!- G_ctrl is an example site irradiance sensor. Users may replace it with",
        "!- a surface-incident irradiance sensor for a specific window orientation.",
        "EnergyManagementSystem:Sensor,",
        "    G_ctrl, Environment, Site Direct Solar Radiation Rate per Area;",
        "",
        _ems_actuators(surface_names),
        "EnergyManagementSystem:ProgramCallingManager,",
        "    SE_EC_Window_Manager,",
        "    BeginTimestepBeforePredictor,",
        "    SE_EC_Window_Switcher;",
        "",
        "EnergyManagementSystem:Program,",
        "    SE_EC_Window_Switcher,"
    ]

    for time_idx, label in enumerate(time_labels, start=1):
        hour = 7 + time_idx
        keyword = "IF" if time_idx == 1 else "ELSEIF"
        blocks.append(f"    {keyword} (Hour == {hour})")
        # State selection inside the time block.
        con_s1 = construction_by_time_state[(time_idx, states[0])]
        con_s2 = construction_by_time_state[(time_idx, states[1])]
        con_s3 = construction_by_time_state[(time_idx, states[2])]
        blocks.append(f"        IF (G_ctrl < {_fmt(t_low)})")
        blocks.append(_set_all_surfaces(surface_names, con_s1))
        blocks.append(f"        ELSEIF (G_ctrl < {_fmt(t_high)})")
        blocks.append(_set_all_surfaces(surface_names, con_s2))
        blocks.append("        ELSE")
        blocks.append(_set_all_surfaces(surface_names, con_s3))
        blocks.append("        ENDIF")
    blocks.append("    ELSE")
    blocks.append(_set_all_surfaces(surface_names, construction_by_time_state[(1, states[0])]))
    blocks.append("    ENDIF;")
    return "\n".join(blocks) + "\n"


def ems_thermochromic_switcher(construction_names: Sequence[str],
                               time_labels: Sequence[str],
                               surface_names: Sequence[str]) -> str:
    """Return EMS skeleton for TC hourly switching.

    The thermochromic state is not selected by EMS. EnergyPlus selects the
    optical state inside WindowMaterial:GlazingGroup:Thermochromic using the
    layer temperature calculated by the heat-balance solver.
    """
    return f"""!- EMS skeleton for thermochromic hourly SE construction switching.
!- EMS selects the hour-specific thermochromic construction only.
!- The thermochromic group itself selects the temperature state in EnergyPlus.
{ems_static_switcher(construction_names, time_labels, surface_names)}
"""


def write_static_snippet(coeffs: pd.DataFrame,
                         prefix: str = "SE_Static",
                         surface_names: Optional[Sequence[str]] = None,
                         include_ems: bool = True) -> str:
    materials, constructions = [], []
    con_names = []
    for idx, row in enumerate(coeffs.to_dict(orient="records"), start=1):
        mat = f"{prefix}_Mat_h{idx:03d}"
        con = f"{prefix}_Con_h{idx:03d}"
        materials.append(window_material_glazing(mat, row))
        constructions.append(construction(con, mat))
        con_names.append(con)
    parts = ["!- Static-window SE material and construction bank.", *materials, *constructions]
    if include_ems:
        parts.append(ems_static_switcher(con_names, list(coeffs["time"].astype(str)), surface_names or ["REPLACE_WITH_WINDOW_SURFACE_NAME"]))
    return "\n\n".join(parts)


def write_electrochromic_snippet(long_coeffs: pd.DataFrame,
                                 states: Sequence[str],
                                 prefix: str = "SE_EC",
                                 surface_names: Optional[Sequence[str]] = None,
                                 include_ems: bool = True,
                                 irradiance_thresholds_w_m2: Tuple[float, float] = (200.0, 400.0)) -> str:
    materials, constructions = [], []
    construction_map: Dict[Tuple[int, str], str] = {}
    times = list(dict.fromkeys(long_coeffs["time"].astype(str).tolist()))
    for time_idx, time_label in enumerate(times, start=1):
        for state in states:
            row = long_coeffs[(long_coeffs["time"].astype(str) == time_label) & (long_coeffs["state"] == state)]
            if row.empty:
                raise ValueError(f"No coefficients found for time={time_label}, state={state}.")
            record = row.iloc[0].to_dict()
            mat = f"{prefix}_Mat_h{time_idx:03d}_{state}"
            con = f"{prefix}_Con_h{time_idx:03d}_{state}"
            materials.append(window_material_glazing(mat, record))
            constructions.append(construction(con, mat))
            construction_map[(time_idx, state)] = con

    parts = ["!- Electrochromic-window SE material and construction bank.", *materials, *constructions]
    if include_ems:
        parts.append(ems_electrochromic_switcher(construction_map, states, times, surface_names or ["REPLACE_WITH_WINDOW_SURFACE_NAME"], irradiance_thresholds_w_m2))
    return "\n\n".join(parts)


def write_thermochromic_snippet(long_coeffs: pd.DataFrame,
                                temperature_states_c: Sequence[float],
                                prefix: str = "SE_TC",
                                surface_names: Optional[Sequence[str]] = None,
                                include_ems: bool = True) -> str:
    materials, groups, constructions = [], [], []
    con_names = []
    times = list(dict.fromkeys(long_coeffs["time"].astype(str).tolist()))
    state_labels = [str(int(t)) if float(t).is_integer() else str(t) for t in temperature_states_c]

    for time_idx, time_label in enumerate(times, start=1):
        temp_material_pairs = []
        for temp_c, state_label in zip(temperature_states_c, state_labels):
            row = long_coeffs[(long_coeffs["time"].astype(str) == time_label) & (long_coeffs["state"].astype(str) == state_label)]
            if row.empty:
                raise ValueError(f"No coefficients found for time={time_label}, temperature state={state_label}.")
            record = row.iloc[0].to_dict()
            mat = f"{prefix}_Mat_h{time_idx:03d}_{state_label}C"
            materials.append(window_material_glazing(mat, record))
            temp_material_pairs.append((float(temp_c), mat))
        group_name = f"{prefix}_Group_h{time_idx:03d}"
        con_name = f"{prefix}_Con_h{time_idx:03d}"
        groups.append(thermochromic_group(group_name, temp_material_pairs))
        constructions.append(construction(con_name, group_name))
        con_names.append(con_name)

    parts = ["!- Thermochromic-window SE material, thermochromic group and construction bank.", *materials, *groups, *constructions]
    if include_ems:
        parts.append(ems_thermochromic_switcher(con_names, times, surface_names or ["REPLACE_WITH_WINDOW_SURFACE_NAME"]))
    return "\n\n".join(parts)

