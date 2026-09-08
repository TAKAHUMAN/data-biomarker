"""Inline AML pharmacodynamic Hill fits for foretinib source figures.

Numeric curve points remain approximate prompt-supplied digitizations. Figure
2G assay matrix, duration, and printed IC50 values are independently verified
against the authorized Wang et al. Cancer Research article.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp
from scipy.optimize import curve_fit

from pk_rcc.constants import FORETINIB_FREE_BASE_MW_G_MOL


CONC_NM_SHARED = np.asarray([0.152, 0.457, 1.372, 4.115, 12.346, 37.037, 111.111, 333.333, 1000.000], dtype=float)
CONC_NM_CETSA = np.asarray([0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0], dtype=float)

PD_PAPER_DOI = "10.1158/0008-5472.CAN-23-1534"
PD_PAPER_PMID = "38231480"
PD_PAPER_PMCID = "PMC10940854"
FIG2G_ASSAY_MATRIX = "100% AML patient plasma"
FIG2G_ASSAY_DURATION_H = 48.0
FIG2G_IC50_PINNING_THRESHOLD_FOLD = 1.5
FIG2G_ASSAY_CONCENTRATION_BASIS = "nominal total concentration added to 100% AML patient plasma"
FIG2G_PKPD_BASIS_STATUS = "APPROXIMATE_MATRIX_MATCHED_TOTAL_TO_TOTAL"
FIG2G_CONCENTRATION_BASIS_LABEL = (
    "clinical measured total plasma nM versus Figure 2G nominal total nM in 100% AML patient plasma"
)
CLINICAL_PK_CONCENTRATION_BASIS = "measured total plasma concentration"
FIG2G_FREE_FRACTION_CORRECTION_APPLIED = False
FIG2G_NO_FU_JUSTIFICATION = (
    "No separate fu correction: the Figure 2G IC50 was measured after dosing cells in 100% AML patient "
    "plasma, so plasma-binding effects are embedded in the nominal total-concentration potency estimate; "
    "applying fu again would double-count plasma protein binding."
)
FIG2A_ASSAY_MATRIX = "RPMI 1640 supplemented with 10% FBS"
FIG2A_ASSAY_DURATION_H = 48.0
FIG2A_ASSAY_CONCENTRATION_BASIS = "nominal concentration in RPMI 1640 supplemented with 10% FBS"

FIG2A = {
    "MV4-11_FLT3-ITD": [54.32, 30.53, 23.26, 17.80, 18.40, 17.97, 17.02, 10.19, 10.44],
    "MOLM13_FLT3-ITD": [88.00, 74.53, 42.25, 21.58, 13.55, 11.15, 8.45, 4.97, 4.11],
    "NB4_FLT3-WT": [102.14, 100.89, 101.36, 97.59, 95.39, 94.41, 100.93, 92.01, 68.21],
    "THP1_FLT3-WT": [97.29, 91.03, 98.92, 100.04, 102.56, 88.61, 96.93, 90.55, 89.27],
    "HL60_FLT3-WT": [99.87, 102.83, 103.54, 109.35, 104.98, 101.23, 93.41, 96.26, 62.26],
    "OCI-AML2_FLT3-WT": [109.74, 116.59, 114.50, 104.64, 108.25, 98.24, 89.55, 87.66, 69.17],
    "OCI-AML3_FLT3-WT": [111.29, 109.23, 101.73, 107.03, 101.51, 107.39, 90.44, 72.47, 64.13],
    "K562_FLT3-WT": [91.89, 84.37, 91.90, 91.58, 94.09, 89.95, 91.47, 67.73, 37.90],
}

FIG2A_PRINTED_IC50_NM = {
    "MV4-11": {"Quizartinib": 0.71, "Gilteritinib": 1.40, "Foretinib": 0.16},
    "MOLM13": {"Quizartinib": 1.38, "Gilteritinib": 3.12, "Foretinib": 0.89},
}

FIG1I = {
    "FLT3_stabilization_percent": [4.36, 13.34, 25.22, 29.35, 43.46, 97.82, 114.42],
    "lower_bound": [1.94, 4.01, 20.80, 17.18, 31.91, 83.33, 108.66],
    "upper_bound": [8.91, 22.61, 29.84, 41.47, 55.17, 112.53, 119.77],
}

FIG4A = {
    "BaF3_IL3-dependent_control": [93.81, 100.01, 101.64, 100.36, 99.82, 99.56, 98.78, 96.54, 90.76],
    "BaF3_FLT3-ITD": [108.61, 99.00, 33.00, 5.00, 0.50, 0.50, 0.50, 0.50, 0.50],
    "BaF3_FLT3-ITD-D835Y": [98.12, 105.72, 106.13, 60.04, 34.74, 8.61, 7.01, 2.66, 0.94],
    "BaF3_FLT3-ITD-D835V": [103.54, 103.93, 97.61, 93.04, 63.59, 16.94, 14.04, 5.36, 2.08],
    "BaF3_FLT3-ITD-Y842C": [100.30, 92.36, 77.65, 40.23, 7.07, 8.92, 3.12, 1.70, 2.71],
    "BaF3_FLT3-ITD-F691L": [93.00, 92.66, 66.57, 28.67, 9.08, 5.68, 4.57, 3.80, 3.97],
}

FIG5 = {
    "AML_1_FLT3-ITD": {
        "Foretinib": [102.17, 91.09, 95.59, 96.54, 98.34, 89.62, 54.26, 3.69, 2.16],
        "Gilteritinib": [96.84, 94.13, 88.59, 95.43, 96.56, 92.11, 89.83, 57.71, 6.31],
        "Quizartinib": [89.92, 85.55, 91.29, 98.76, 94.98, 95.58, 92.86, 93.85, 93.99],
    },
    "AML_2_FLT3-ITD": {
        "Foretinib": [86.84, 73.44, 65.12, 50.24, 42.25, 32.68, 30.70, 28.69, 29.53],
        "Gilteritinib": [77.13, 71.44, 67.10, 61.09, 55.27, 51.83, 44.46, 43.96, 36.06],
        "Quizartinib": [80.48, 75.75, 59.44, 58.30, 58.27, 53.86, 49.31, 42.22, 39.06],
    },
    "AML_7_FLT3-ITD": {
        "Foretinib": [65.20, 55.46, 53.78, 52.79, 52.87, 52.61, 48.57, 31.94, 1.14],
        "Gilteritinib": [91.51, 88.80, 83.74, 68.60, 62.14, 51.27, 51.84, 48.99, 44.35],
        "Quizartinib": [79.97, 72.82, 58.68, 51.00, 51.16, 53.99, 53.47, 50.75, 48.49],
    },
    "AML_8_FLT3-ITD": {
        "Foretinib": [85.63, 81.28, 83.53, 89.08, 93.75, 86.09, 23.74, 8.87, 9.09],
        "Gilteritinib": [103.66, 100.35, 110.01, 100.44, 98.22, 89.02, 75.80, 62.93, 55.61],
        "Quizartinib": [100.55, 103.24, 97.06, 104.27, 104.95, 96.26, 98.80, 89.39, 78.22],
    },
    "AML_11_FLT3-D835V": {
        "Foretinib": [84.70, 91.75, 96.16, 94.04, 85.47, 102.30, 71.61, 59.16, 22.99],
        "Gilteritinib": [109.30, 124.92, 114.79, 122.99, 105.90, 108.21, 88.18, 52.72, 18.73],
        "Quizartinib": [91.14, 96.33, 90.50, 91.13, 92.17, 93.64, 94.87, 107.31, 115.19],
    },
    "AML_12_FLT3-D835E": {
        "Foretinib": [81.18, 69.63, 60.61, 43.42, 38.31, 37.22, 36.49, 34.94, 36.25],
        "Gilteritinib": [84.93, 74.72, 56.30, 41.35, 35.51, 38.97, 38.41, 40.20, 38.39],
        "Quizartinib": [92.72, 91.10, 91.38, 81.71, 69.07, 45.65, 40.31, 37.32, 33.39],
    },
    "AML_9_FLT3-ITD-D835Y": {
        "Foretinib": [87.62, 84.93, 87.69, 81.08, 76.42, 71.30, 54.10, 7.82, 4.48],
        "Gilteritinib": [100.64, 96.56, 102.20, 101.20, 93.35, 84.18, 46.90, 21.57, 12.39],
        "Quizartinib": [92.80, 91.76, 96.95, 93.51, 97.97, 95.45, 85.93, 88.87, 88.02],
    },
    "AML_10_FLT3-ITD-D835V": {
        "Foretinib": [52.79, 35.17, 35.15, 35.25, 32.77, 28.46, 25.52, 21.36, 1.23],
        "Gilteritinib": [80.37, 70.81, 56.21, 38.83, 30.46, 29.78, 22.96, 25.54, 23.92],
        "Quizartinib": [110.49, 115.12, 112.48, 109.14, 104.00, 93.96, 82.03, 64.08, 36.73],
    },
}

FIG2G = {
    "MV4-11": {
        "Foretinib": [118.45, 115.22, 104.83, 67.22, 42.58, 29.10, 13.19, 7.34, 5.17],
        "Gilteritinib": [100.40, 100.28, 100.11, 90.42, 88.99, 74.06, 49.14, 14.46, 2.60],
    },
    "MOLM13": {
        "Foretinib": [96.88, 92.81, 97.72, 77.93, 69.03, 44.49, 16.83, 6.89, 2.96],
        "Gilteritinib": [99.44, 95.71, 102.27, 105.93, 105.50, 88.03, 52.00, 19.43, 4.89],
    },
}

FIG2G_REPORTED_IC50_NM = {
    "MV4-11": {"Foretinib": 11.98, "Gilteritinib": 92.39},
    "MOLM13": {"Foretinib": 25.57, "Gilteritinib": 124.30},
}

FORETINIB_MW_G_MOL_FROM_PK_RCC = FORETINIB_FREE_BASE_MW_G_MOL
PD_ASSAY_DURATION_DAYS = 2.0
DEFAULT_AML_NET_GROWTH_RATE_PER_DAY = 0.03
MIN_AML_NET_GROWTH_RATE_PER_DAY = 0.02
MAX_AML_NET_GROWTH_RATE_PER_DAY = 0.05
DEFAULT_KILL_MAX_PER_DAY = 0.35
MIN_KILL_MAX_PER_DAY = 0.20
MAX_KILL_MAX_PER_DAY = 0.50


@dataclass(frozen=True)
class SeriesSpec:
    figure: str
    model: str
    mutation_or_condition: str
    drug: str
    endpoint: str
    conc_nM: np.ndarray
    response_pct: np.ndarray
    direction: str
    confidence: str
    source_note: str
    printed_IC50_nM: float = math.nan
    lower_bound: np.ndarray | None = None
    upper_bound: np.ndarray | None = None
    fit_variant: str = "unweighted"
    weights: np.ndarray | None = None


def _cell_key(model: str) -> str:
    if model.startswith("MV4-11"):
        return "MV4-11"
    if model.startswith("MOLM13"):
        return "MOLM13"
    return model


def _condition_from_model(model: str) -> str:
    if "_" not in model:
        return model
    return model.split("_", 1)[1]


def _as_array(values: Iterable[float]) -> np.ndarray:
    return np.asarray(list(values), dtype=float)


def source_series_specs() -> list[SeriesSpec]:
    specs: list[SeriesSpec] = []
    for model, response in FIG2A.items():
        cell_key = _cell_key(model)
        printed = FIG2A_PRINTED_IC50_NM.get(cell_key, {}).get("Foretinib", math.nan)
        specs.append(
            SeriesSpec(
                figure="Fig2A",
                model=model,
                mutation_or_condition=_condition_from_model(model),
                drug="Foretinib",
                endpoint="48h viability percent",
                conc_nM=CONC_NM_SHARED,
                response_pct=_as_array(response),
                direction="decreasing",
                confidence="approximate_digitized",
                source_note="Figure 2A digitized foretinib AML cell-line viability; inferred shared concentration grid.",
                printed_IC50_nM=printed,
            )
        )
    for model, response in FIG4A.items():
        confidence = "low" if model == "BaF3_FLT3-ITD" else "approximate_digitized"
        specs.append(
            SeriesSpec(
                figure="Fig4A",
                model=model,
                mutation_or_condition=model.replace("BaF3_", ""),
                drug="Foretinib",
                endpoint="48h viability percent",
                conc_nM=CONC_NM_SHARED,
                response_pct=_as_array(response),
                direction="decreasing",
                confidence=confidence,
                source_note="Figure 4A digitized Ba/F3 resistance-mutant viability; inferred shared concentration grid.",
            )
        )
    for model, drugs in FIG5.items():
        for drug, response in drugs.items():
            specs.append(
                SeriesSpec(
                    figure="Fig5",
                    model=model,
                    mutation_or_condition=_condition_from_model(model),
                    drug=drug,
                    endpoint="primary AML blast 48h viability percent",
                    conc_nM=CONC_NM_SHARED,
                    response_pct=_as_array(response),
                    direction="decreasing",
                    confidence="approximate_digitized",
                    source_note="Figure 5 digitized primary AML blast viability; inferred shared concentration grid.",
                )
            )
    for model, drugs in FIG2G.items():
        for drug, response in drugs.items():
            specs.append(
                SeriesSpec(
                    figure="Fig2G",
                    model=model,
                    mutation_or_condition=FIG2G_ASSAY_MATRIX,
                    drug=drug,
                    endpoint=f"{FIG2G_ASSAY_MATRIX} {FIG2G_ASSAY_DURATION_H:g}h viability percent",
                    conc_nM=CONC_NM_SHARED,
                    response_pct=_as_array(response),
                    direction="decreasing",
                    confidence="approximate_digitized",
                    source_note=(
                        "Figure 2G digitized plasma-context viability; assay matrix and 48 h duration verified "
                        f"from Wang et al. ({PD_PAPER_DOI}); shared concentration grid remains inferred."
                    ),
                    printed_IC50_nM=FIG2G_REPORTED_IC50_NM[model][drug],
                )
            )
    cetsa = _as_array(FIG1I["FLT3_stabilization_percent"])
    lower = _as_array(FIG1I["lower_bound"])
    upper = _as_array(FIG1I["upper_bound"])
    spread = 0.5 * (upper - lower)
    base_kwargs = dict(
        figure="Fig1I",
        model="FLT3_CETSA_51.1C",
        mutation_or_condition="relative FLT3 band intensity at 51.1C",
        drug="Foretinib",
        endpoint="FLT3 stabilization percent",
        conc_nM=CONC_NM_CETSA,
        response_pct=cetsa,
        direction="increasing",
        confidence="approximate_digitized_with_bounds",
        source_note="Figure 1I digitized CETSA stabilization, explicit printed concentration grid.",
        lower_bound=lower,
        upper_bound=upper,
    )
    specs.append(SeriesSpec(**base_kwargs, fit_variant="unweighted"))
    specs.append(SeriesSpec(**base_kwargs, fit_variant="weighted_bounds", weights=1.0 / spread))
    return specs


def hill_response_log10(log10_conc_nM: np.ndarray, etop: float, ebottom: float, log10_halfmax_nM: float, h: float, direction: str) -> np.ndarray:
    conc = np.power(10.0, np.asarray(log10_conc_nM, dtype=float))
    halfmax = 10.0**float(log10_halfmax_nM)
    with np.errstate(over="ignore", invalid="ignore"):
        if direction == "increasing":
            ch = np.power(conc, h)
            hh = halfmax**h
            return ebottom + (etop - ebottom) * ch / (hh + ch)
        return ebottom + (etop - ebottom) / (1.0 + np.power(conc / halfmax, h))


def fit_hill(conc: np.ndarray, resp: np.ndarray, direction: str, weights: np.ndarray | None = None) -> dict[str, float | str]:
    """Fit a bounded four-parameter Hill model on a log10 concentration axis."""
    conc = np.asarray(conc, dtype=float)
    resp = np.asarray(resp, dtype=float)
    if direction not in {"decreasing", "increasing"}:
        raise ValueError("direction must be 'decreasing' or 'increasing'")
    if np.any(~np.isfinite(conc)) or np.any(~np.isfinite(resp)) or np.any(conc <= 0):
        return _failed_fit("nonpositive_or_nonfinite_input")

    logc = np.log10(conc)
    log_lower = math.log10(float(np.min(conc)) / 100.0)
    log_upper = math.log10(float(np.max(conc)) * 100.0)
    max_resp = float(np.max(resp))
    min_resp = float(np.min(resp))
    if direction == "increasing":
        etop0 = float(np.clip(max(100.0, max_resp), 0.0, 150.0))
        ebottom0 = float(np.clip(min_resp, 0.0, 150.0))
    else:
        etop0 = float(np.clip(max(100.0, max_resp), 0.0, 150.0))
        ebottom0 = float(np.clip(min_resp, 0.0, 150.0))
    p0 = [etop0, ebottom0, 0.5 * (log_lower + log_upper), 1.0]

    sigma = None
    if weights is not None:
        precision = np.asarray(weights, dtype=float)
        if np.any(~np.isfinite(precision)) or np.any(precision <= 0):
            return _failed_fit("invalid_weights")
        sigma = 1.0 / precision

    try:
        popt, _pcov = curve_fit(
            lambda x, etop, ebottom, log_half, h: hill_response_log10(x, etop, ebottom, log_half, h, direction),
            logc,
            resp,
            p0=p0,
            bounds=([0.0, 0.0, log_lower, 0.2], [150.0, 150.0, log_upper, 6.0]),
            sigma=sigma,
            absolute_sigma=False,
            maxfev=50000,
        )
        pred = hill_response_log10(logc, *popt, direction)
        ss_res = float(np.sum((resp - pred) ** 2))
        ss_tot = float(np.sum((resp - np.mean(resp)) ** 2))
        r2 = math.nan if ss_tot <= 0 else 1.0 - ss_res / ss_tot
        halfmax = 10.0 ** float(popt[2])
        return {
            "fitted_IC50_nM": halfmax,
            "hill_slope": float(popt[3]),
            "Etop": float(popt[0]),
            "Ebottom": float(popt[1]),
            "R2": float(r2),
            "fit_status": "success",
            "failure_reason": "",
        }
    except Exception as exc:  # pragma: no cover - exercised by failed-fit guardrails
        return _failed_fit(type(exc).__name__)


def fit_inhibitory_viability_hill(
    conc: np.ndarray,
    resp: np.ndarray,
    *,
    fixed_etop_pct: float = 100.0,
    fixed_ic50_nM: float | None = None,
    cap_supra_etop_for_fit: bool = True,
) -> dict[str, float | str | bool | int]:
    """Fit a biologically bounded viability curve, optionally fixing IC50 to the paper value.

    Original digitized responses are retained for residual diagnostics. Values above
    the normalized no-drug plateau are capped only in the fitting objective because
    they represent digitization/experimental noise rather than viability above the
    model's 100% baseline.
    """
    conc = np.asarray(conc, dtype=float)
    observed = np.asarray(resp, dtype=float)
    if np.any(~np.isfinite(conc)) or np.any(~np.isfinite(observed)) or np.any(conc <= 0):
        return {**_failed_fit("nonpositive_or_nonfinite_input"), "IC50_fixed": fixed_ic50_nM is not None}
    if fixed_etop_pct <= 0.0:
        return {**_failed_fit("invalid_fixed_etop"), "IC50_fixed": fixed_ic50_nM is not None}
    if fixed_ic50_nM is not None and (not np.isfinite(fixed_ic50_nM) or fixed_ic50_nM <= 0.0):
        return {**_failed_fit("invalid_fixed_ic50"), "IC50_fixed": True}

    fit_response = np.minimum(observed, fixed_etop_pct) if cap_supra_etop_for_fit else observed.copy()
    n_capped = int(np.sum(observed > fixed_etop_pct)) if cap_supra_etop_for_fit else 0
    logc = np.log10(conc)
    log_lower = math.log10(float(np.min(conc)) / 100.0)
    log_upper = math.log10(float(np.max(conc)) * 100.0)
    ebottom0 = float(np.clip(np.min(fit_response), 0.0, fixed_etop_pct))

    try:
        if fixed_ic50_nM is None:
            p0 = [ebottom0, 0.5 * (log_lower + log_upper), 1.0]
            popt, _pcov = curve_fit(
                lambda x, ebottom, log_half, h: hill_response_log10(
                    x, fixed_etop_pct, ebottom, log_half, h, "decreasing"
                ),
                logc,
                fit_response,
                p0=p0,
                bounds=([0.0, log_lower, 0.2], [fixed_etop_pct, log_upper, 6.0]),
                maxfev=50000,
            )
            ebottom, log_half, hill_slope = (float(value) for value in popt)
            ic50_nM = 10.0**log_half
        else:
            log_half = math.log10(float(fixed_ic50_nM))
            p0 = [ebottom0, 1.0]
            popt, _pcov = curve_fit(
                lambda x, ebottom, h: hill_response_log10(
                    x, fixed_etop_pct, ebottom, log_half, h, "decreasing"
                ),
                logc,
                fit_response,
                p0=p0,
                bounds=([0.0, 0.2], [fixed_etop_pct, 6.0]),
                maxfev=50000,
            )
            ebottom, hill_slope = (float(value) for value in popt)
            ic50_nM = float(fixed_ic50_nM)

        predicted = hill_response_log10(logc, fixed_etop_pct, ebottom, log_half, hill_slope, "decreasing")
        observed_ss_res = float(np.sum((observed - predicted) ** 2))
        observed_ss_tot = float(np.sum((observed - np.mean(observed)) ** 2))
        objective_ss_res = float(np.sum((fit_response - predicted) ** 2))
        objective_ss_tot = float(np.sum((fit_response - np.mean(fit_response)) ** 2))
        ebottom_at_lower_bound = ebottom <= max(1e-6, fixed_etop_pct * 1e-6)
        return {
            "fitted_IC50_nM": float(ic50_nM),
            "hill_slope": hill_slope,
            "Etop": float(fixed_etop_pct),
            "Ebottom": ebottom,
            "R2": math.nan if observed_ss_tot <= 0 else 1.0 - observed_ss_res / observed_ss_tot,
            "objective_R2": math.nan if objective_ss_tot <= 0 else 1.0 - objective_ss_res / objective_ss_tot,
            "fit_status": "success",
            "failure_reason": "",
            "IC50_fixed": fixed_ic50_nM is not None,
            "n_supra_etop_points_capped_for_fit": n_capped,
            "response_cap_applied_for_fit_only": bool(cap_supra_etop_for_fit),
            "ebottom_boundary_status": (
                "AT_LOWER_BOUND_NOT_RELIABLY_ESTIMATED"
                if ebottom_at_lower_bound
                else "INTERIOR_BOUNDED_ESTIMATE"
            ),
            "supra_etop_capping_status": (
                f"FIT_OBJECTIVE_CAPPED_{n_capped}_SUPRA_100_PERCENT_POINTS"
                if n_capped > 0
                else "NO_SUPRA_ETOP_POINTS_CAPPED"
            ),
            "pd_fit_interpretation": (
                "IC50 and slope mapping retained; boundary Ebottom is a biological floor constraint, not a precise estimate."
                if ebottom_at_lower_bound
                else "Bounded viability mapping with original observations retained for residual diagnostics."
            ),
        }
    except Exception as exc:  # pragma: no cover - exercised by failed-fit guardrails
        return {
            **_failed_fit(type(exc).__name__),
            "objective_R2": math.nan,
            "IC50_fixed": fixed_ic50_nM is not None,
            "n_supra_etop_points_capped_for_fit": n_capped,
            "response_cap_applied_for_fit_only": bool(cap_supra_etop_for_fit),
            "ebottom_boundary_status": "NOT_AVAILABLE_FIT_FAILED",
            "supra_etop_capping_status": (
                f"FIT_OBJECTIVE_CAPPED_{n_capped}_SUPRA_100_PERCENT_POINTS"
                if n_capped > 0
                else "NO_SUPRA_ETOP_POINTS_CAPPED"
            ),
            "pd_fit_interpretation": "Fit failed; no parameter interpretation.",
        }


def _failed_fit(reason: str) -> dict[str, float | str]:
    return {
        "fitted_IC50_nM": math.nan,
        "hill_slope": math.nan,
        "Etop": math.nan,
        "Ebottom": math.nan,
        "R2": math.nan,
        "fit_status": "failed",
        "failure_reason": reason,
    }


def _predict(conc_nM: np.ndarray, fit_row: pd.Series, direction: str) -> np.ndarray:
    if str(fit_row["fit_status"]) != "success":
        return np.full(len(conc_nM), np.nan)
    return hill_response_log10(
        np.log10(np.asarray(conc_nM, dtype=float)),
        float(fit_row["Etop"]),
        float(fit_row["Ebottom"]),
        math.log10(float(fit_row["fitted_IC50_nM"])),
        float(fit_row["hill_slope"]),
        direction,
    )


def predict_response_from_fit(conc_nM: np.ndarray | pd.Series, fit_row: pd.Series) -> np.ndarray:
    """Project concentrations through one fitted PD curve, preserving the zero-dose limit."""
    conc = np.asarray(conc_nM, dtype=float)
    if str(fit_row["fit_status"]) != "success":
        return np.full(len(conc), np.nan)

    direction = str(fit_row["direction"])
    pred = np.full(len(conc), np.nan)
    positive = np.isfinite(conc) & (conc > 0)
    zero_or_below = np.isfinite(conc) & ~positive

    if direction == "increasing":
        pred[zero_or_below] = float(fit_row["Ebottom"])
    else:
        pred[zero_or_below] = float(fit_row["Etop"])

    if positive.any():
        pred[positive] = hill_response_log10(
            np.log10(conc[positive]),
            float(fit_row["Etop"]),
            float(fit_row["Ebottom"]),
            math.log10(float(fit_row["fitted_IC50_nM"])),
            float(fit_row["hill_slope"]),
            direction,
        )
    return pred


def _fit_value(fit_row: object, key: str, default: object = math.nan) -> object:
    if isinstance(fit_row, pd.Series):
        return fit_row.get(key, default)
    if isinstance(fit_row, dict):
        return fit_row.get(key, default)
    return getattr(fit_row, key, default)


def estimate_aml_growth_rate_from_controls() -> dict[str, float | str]:
    """Estimate a bounded AML net-growth proxy from low-dose FLT3-WT Fig2A controls.

    The inline source contains 48 h endpoint viability curves, not untreated
    longitudinal cell counts. We therefore use the low-dose FLT3-WT series as a
    control-like proxy and clip the result to the narrow net-growth range used
    for normalized viability recovery.
    """
    control_values: list[float] = []
    for model, response in FIG2A.items():
        if "FLT3-WT" in model:
            control_values.extend(float(value) for value in response[:5])
    if not control_values:
        return {
            "k_g_per_day": DEFAULT_AML_NET_GROWTH_RATE_PER_DAY,
            "raw_k_g_per_day": math.nan,
            "control_response_median_pct": math.nan,
            "growth_rate_source": "DEFAULT_NO_CONTROL_PROXY_AVAILABLE",
        }

    median_response = float(np.nanmedian(np.asarray(control_values, dtype=float)))
    raw_growth = max(0.0, (median_response - 100.0) / 100.0 / PD_ASSAY_DURATION_DAYS)
    clipped_growth = float(np.clip(raw_growth, MIN_AML_NET_GROWTH_RATE_PER_DAY, MAX_AML_NET_GROWTH_RATE_PER_DAY))
    return {
        "k_g_per_day": clipped_growth,
        "raw_k_g_per_day": float(raw_growth),
        "control_response_median_pct": median_response,
        "growth_rate_source": "FIG2A_LOW_DOSE_FLT3_WT_CONTROL_PROXY_CLIPPED",
    }


def _instantaneous_hill_response_pct(conc_nM: float, fit_row: object) -> float:
    direction = str(_fit_value(fit_row, "direction", "decreasing"))
    if not np.isfinite(conc_nM) or conc_nM <= 0.0:
        return float(_fit_value(fit_row, "Ebottom" if direction == "increasing" else "Etop"))
    value = hill_response_log10(
        np.asarray([math.log10(float(conc_nM))], dtype=float),
        float(_fit_value(fit_row, "Etop")),
        float(_fit_value(fit_row, "Ebottom")),
        math.log10(float(_fit_value(fit_row, "fitted_IC50_nM"))),
        float(_fit_value(fit_row, "hill_slope")),
        direction,
    )[0]
    return float(value)


def _hill_kill_fraction(conc_nM: float, fit_row: object) -> float:
    baseline = float(_fit_value(fit_row, "Etop"))
    floor = float(_fit_value(fit_row, "Ebottom"))
    response = _instantaneous_hill_response_pct(conc_nM, fit_row)
    denominator = baseline - floor
    if not np.isfinite(denominator) or denominator <= 1e-9:
        denominator = max(abs(baseline), 1e-9)
    return float(np.clip((baseline - response) / denominator, 0.0, 1.0))


def estimate_kill_max_from_hill_fit(fit_row: object, k_g_per_day: float | None = None) -> dict[str, float | str]:
    """Estimate a bounded max kill rate from the 48 h high-dose Hill response."""
    k_g = float(k_g_per_day) if k_g_per_day is not None else float(estimate_aml_growth_rate_from_controls()["k_g_per_day"])
    max_conc_nM = float(np.max(CONC_NM_SHARED))
    baseline = max(float(_fit_value(fit_row, "Etop")), 1e-6)
    carrying_capacity = max(100.0, baseline)
    high_response = _instantaneous_hill_response_pct(max_conc_nM, fit_row)
    target = float(np.clip(high_response, 0.1, carrying_capacity))
    effect_fraction = _hill_kill_fraction(max_conc_nM, fit_row)
    if not np.isfinite(effect_fraction) or effect_fraction <= 1e-6:
        raw_kill = DEFAULT_KILL_MAX_PER_DAY
        source = "DEFAULT_NO_HIGH_DOSE_INHIBITION_SIGNAL"
    else:
        target_ratio = float(np.clip(target / baseline, 1e-6, 1.0))
        mean_growth_factor = max(0.0, 1.0 - 0.5 * (baseline + target) / carrying_capacity)
        raw_kill = (math.log(1.0 / target_ratio) / PD_ASSAY_DURATION_DAYS + k_g * mean_growth_factor) / effect_fraction
        if not np.isfinite(raw_kill) or raw_kill <= 0.0:
            raw_kill = DEFAULT_KILL_MAX_PER_DAY
            source = "DEFAULT_INVALID_HIGH_DOSE_KILL_ESTIMATE"
        else:
            source = "FITTED_FROM_48H_HIGH_DOSE_HILL_RESPONSE_CLIPPED"
    clipped_kill = float(np.clip(raw_kill, MIN_KILL_MAX_PER_DAY, MAX_KILL_MAX_PER_DAY))
    return {
        "k_kill_max_per_day": clipped_kill,
        "raw_k_kill_max_per_day": float(raw_kill),
        "high_dose_response_pct": float(high_response),
        "high_dose_kill_fraction": float(effect_fraction),
        "kill_parameter_source": source,
    }


def simulate_cell_kill_projection(
    days: np.ndarray | pd.Series,
    conc_nM: np.ndarray | pd.Series,
    fit_row: object,
    k_g_per_day: float | None = None,
    k_kill_max_per_day: float | None = None,
) -> pd.DataFrame:
    """Integrate dN/dt = k_g*N*(1 - N/Nmax) - kkill(t)*N over a PK profile."""
    t_eval = np.asarray(days, dtype=float)
    concentrations = np.asarray(conc_nM, dtype=float)
    if len(t_eval) != len(concentrations):
        raise ValueError("days and conc_nM must have the same length")
    if len(t_eval) == 0:
        return pd.DataFrame()

    order = np.argsort(t_eval)
    sorted_days = t_eval[order]
    sorted_conc = concentrations[order]
    growth = estimate_aml_growth_rate_from_controls()
    k_g = float(k_g_per_day) if k_g_per_day is not None else float(growth["k_g_per_day"])
    kill_params = estimate_kill_max_from_hill_fit(fit_row, k_g)
    k_kill_max = float(k_kill_max_per_day) if k_kill_max_per_day is not None else float(kill_params["k_kill_max_per_day"])

    baseline = max(float(_fit_value(fit_row, "Etop")), 1e-6)
    carrying_capacity = max(100.0, baseline)
    y0 = [float(np.clip(baseline, 0.0, carrying_capacity))]

    def rhs(t: float, y: np.ndarray) -> list[float]:
        n_cells = max(float(y[0]), 0.0)
        c_t = float(np.interp(t, sorted_days, sorted_conc, left=sorted_conc[0], right=sorted_conc[-1]))
        kill_fraction = _hill_kill_fraction(c_t, fit_row)
        growth_term = k_g * n_cells * (1.0 - n_cells / carrying_capacity)
        kill_term = k_kill_max * kill_fraction * n_cells
        return [growth_term - kill_term]

    if len(sorted_days) == 1 or float(sorted_days[-1]) == float(sorted_days[0]):
        projected = np.asarray(y0 * len(sorted_days), dtype=float).reshape(-1)
    else:
        median_step = float(np.nanmedian(np.diff(np.unique(sorted_days)))) if len(np.unique(sorted_days)) > 1 else 0.25
        max_step = max(min(median_step, 0.25), 0.05)
        sol = solve_ivp(
            rhs,
            (float(sorted_days[0]), float(sorted_days[-1])),
            y0,
            t_eval=sorted_days,
            method="RK45",
            rtol=1e-6,
            atol=1e-8,
            max_step=max_step,
        )
        if not sol.success:
            raise RuntimeError(f"Cell-kill ODE integration failed: {sol.message}")
        projected = np.clip(sol.y[0], 0.0, carrying_capacity)

    instantaneous = np.asarray([_instantaneous_hill_response_pct(float(c), fit_row) for c in sorted_conc], dtype=float)
    kill_fraction = np.asarray([_hill_kill_fraction(float(c), fit_row) for c in sorted_conc], dtype=float)
    out = pd.DataFrame(
        {
            "day": sorted_days,
            "conc_nM": sorted_conc,
            "instantaneous_hill_response_pct": instantaneous,
            "hill_kill_fraction": kill_fraction,
            "k_kill_t_per_day": kill_fraction * k_kill_max,
            "projected_viability_pct": projected,
            "k_g_per_day": k_g,
            "raw_k_g_per_day": float(growth["raw_k_g_per_day"]),
            "control_response_median_pct": float(growth["control_response_median_pct"]),
            "k_kill_max_per_day": k_kill_max,
            "raw_k_kill_max_per_day": float(kill_params["raw_k_kill_max_per_day"]),
            "carrying_capacity_pct": carrying_capacity,
            "growth_rate_source": str(growth["growth_rate_source"]),
            "kill_parameter_source": str(kill_params["kill_parameter_source"]),
        }
    )
    return out


def growth_kill_parameter_table(fit_results: pd.DataFrame) -> pd.DataFrame:
    growth = estimate_aml_growth_rate_from_controls()
    rows = []
    foretinib_viability = fit_results[
        fit_results["drug"].eq("Foretinib")
        & fit_results["fit_status"].eq("success")
        & fit_results["fit_variant"].eq("unweighted")
        & fit_results["endpoint"].str.contains("viability", case=False, na=False)
    ]
    for _, fit_row in foretinib_viability.iterrows():
        kill = estimate_kill_max_from_hill_fit(fit_row, float(growth["k_g_per_day"]))
        rows.append(
            {
                "figure": fit_row["figure"],
                "model": fit_row["model"],
                "mutation_or_condition": fit_row["mutation_or_condition"],
                "endpoint": fit_row["endpoint"],
                "fit_variant": fit_row["fit_variant"],
                "fitted_IC50_nM": float(fit_row["fitted_IC50_nM"]),
                "hill_slope": float(fit_row["hill_slope"]),
                "k_g_per_day": float(growth["k_g_per_day"]),
                "raw_k_g_per_day": float(growth["raw_k_g_per_day"]),
                "control_response_median_pct": float(growth["control_response_median_pct"]),
                "k_kill_max_per_day": float(kill["k_kill_max_per_day"]),
                "raw_k_kill_max_per_day": float(kill["raw_k_kill_max_per_day"]),
                "high_dose_response_pct": float(kill["high_dose_response_pct"]),
                "high_dose_kill_fraction": float(kill["high_dose_kill_fraction"]),
                "growth_rate_source": str(growth["growth_rate_source"]),
                "kill_parameter_source": str(kill["kill_parameter_source"]),
                "model_note": "Parameters drive the growth+kill ODE projection; source curves are 48 h endpoint viability, not time-course efficacy.",
            }
        )
    return pd.DataFrame(rows)

def source_points_table() -> pd.DataFrame:
    rows = []
    seen = set()
    for spec in source_series_specs():
        source_key = (spec.figure, spec.model, spec.drug, spec.endpoint)
        if source_key in seen:
            continue
        seen.add(source_key)
        for idx, (conc, response) in enumerate(zip(spec.conc_nM, spec.response_pct)):
            rows.append(
                {
                    "figure": spec.figure,
                    "model": spec.model,
                    "mutation_or_condition": spec.mutation_or_condition,
                    "drug": spec.drug,
                    "endpoint": spec.endpoint,
                    "point_index": idx,
                    "concentration_nM": float(conc),
                    "response_pct": float(response),
                    "lower_bound_pct": float(spec.lower_bound[idx]) if spec.lower_bound is not None else math.nan,
                    "upper_bound_pct": float(spec.upper_bound[idx]) if spec.upper_bound is not None else math.nan,
                    "confidence": spec.confidence,
                    "source_type": "DIGITIZED_APPROXIMATE",
                    "source_note": spec.source_note,
                }
            )
    return pd.DataFrame(rows)


def fit_all_series() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    fit_rows = []
    point_rows = []
    grid_rows = []
    for spec in source_series_specs():
        fit = fit_hill(spec.conc_nM, spec.response_pct, spec.direction, weights=spec.weights)
        printed = float(spec.printed_IC50_nM) if pd.notna(spec.printed_IC50_nM) else math.nan
        ratio = float(fit["fitted_IC50_nM"]) / printed if fit["fit_status"] == "success" and pd.notna(printed) else math.nan
        fit_row = {
            "figure": spec.figure,
            "model": spec.model,
            "mutation_or_condition": spec.mutation_or_condition,
            "drug": spec.drug,
            "endpoint": spec.endpoint,
            "n_points": len(spec.conc_nM),
            "fitted_IC50_nM": fit["fitted_IC50_nM"],
            "hill_slope": fit["hill_slope"],
            "Etop": fit["Etop"],
            "Ebottom": fit["Ebottom"],
            "R2": fit["R2"],
            "fit_status": fit["fit_status"],
            "confidence": spec.confidence,
            "printed_IC50_nM": printed,
            "fitted_vs_printed_ratio": ratio,
            "fit_variant": spec.fit_variant,
            "direction": spec.direction,
            "failure_reason": fit["failure_reason"],
            "source_type": "FITTED_TO_DIGITIZED_APPROXIMATE",
            "model_note": "Printed IC50 anchors are reported side-by-side and are never overwritten by fitted values.",
        }
        fit_rows.append(fit_row)
        fit_series = pd.Series(fit_row)
        pred = _predict(spec.conc_nM, fit_series, spec.direction)
        for idx, (conc, response, fitted) in enumerate(zip(spec.conc_nM, spec.response_pct, pred)):
            point_rows.append(
                {
                    "figure": spec.figure,
                    "model": spec.model,
                    "mutation_or_condition": spec.mutation_or_condition,
                    "drug": spec.drug,
                    "endpoint": spec.endpoint,
                    "fit_variant": spec.fit_variant,
                    "point_index": idx,
                    "concentration_nM": float(conc),
                    "response_pct": float(response),
                    "fitted_response_pct": float(fitted) if np.isfinite(fitted) else math.nan,
                    "lower_bound_pct": float(spec.lower_bound[idx]) if spec.lower_bound is not None else math.nan,
                    "upper_bound_pct": float(spec.upper_bound[idx]) if spec.upper_bound is not None else math.nan,
                    "confidence": spec.confidence,
                    "source_type": "DIGITIZED_APPROXIMATE_WITH_FIT",
                }
            )
        if fit["fit_status"] == "success":
            grid = np.geomspace(float(np.min(spec.conc_nM)), float(np.max(spec.conc_nM)), 160)
            grid_pred = _predict(grid, fit_series, spec.direction)
            for conc, fitted in zip(grid, grid_pred):
                grid_rows.append(
                    {
                        "figure": spec.figure,
                        "model": spec.model,
                        "mutation_or_condition": spec.mutation_or_condition,
                        "drug": spec.drug,
                        "endpoint": spec.endpoint,
                        "fit_variant": spec.fit_variant,
                        "concentration_nM": float(conc),
                        "fitted_response_pct": float(fitted),
                        "confidence": spec.confidence,
                    }
                )
    return pd.DataFrame(fit_rows), pd.DataFrame(point_rows), pd.DataFrame(grid_rows)


def potency_comparison_table(fit_results: pd.DataFrame) -> pd.DataFrame:
    long_rows = []
    fitted = fit_results[
        fit_results["fit_status"].eq("success")
        & fit_results["endpoint"].str.contains("viability", case=False, na=False)
        & fit_results["fit_variant"].eq("unweighted")
    ].copy()
    for row in fitted.itertuples(index=False):
        long_rows.append(
            {
                "figure": row.figure,
                "model": row.model,
                "mutation_or_condition": row.mutation_or_condition,
                "drug": row.drug,
                "ic50_source": "fitted_digitized_curve",
                "ic50_nM": row.fitted_IC50_nM,
            }
        )
    for model, drugs in FIG2A_PRINTED_IC50_NM.items():
        for drug, ic50 in drugs.items():
            long_rows.append(
                {
                    "figure": "Fig2A",
                    "model": model,
                    "mutation_or_condition": "FLT3-ITD",
                    "drug": drug,
                    "ic50_source": "printed_authoritative",
                    "ic50_nM": ic50,
                }
            )
    for model, drugs in FIG2G_REPORTED_IC50_NM.items():
        for drug, ic50 in drugs.items():
            long_rows.append(
                {
                    "figure": "Fig2G",
                    "model": model,
                    "mutation_or_condition": FIG2G_ASSAY_MATRIX,
                    "drug": drug,
                    "ic50_source": "printed_authoritative",
                    "ic50_nM": ic50,
                }
            )
    long = pd.DataFrame(long_rows)
    rows = []
    group_cols = ["figure", "model", "mutation_or_condition", "ic50_source"]
    for keys, group in long.groupby(group_cols, sort=False):
        values = group.set_index("drug")["ic50_nM"].to_dict()
        if "Foretinib" not in values:
            continue
        for comparator in ["Gilteritinib", "Quizartinib"]:
            if comparator not in values:
                continue
            rows.append(
                {
                    "figure": keys[0],
                    "model": keys[1],
                    "mutation_or_condition": keys[2],
                    "ic50_source": keys[3],
                    "comparator_drug": comparator,
                    "foretinib_IC50_nM": float(values["Foretinib"]),
                    "comparator_IC50_nM": float(values[comparator]),
                    "potency_ratio_comparator_over_foretinib": float(values[comparator] / values["Foretinib"]),
                    "source_type": "DERIVED_FROM_EXISTING_IC50_VALUES_ONLY",
                }
            )
    return pd.DataFrame(rows)


def pd_run_summary(fit_results: pd.DataFrame) -> pd.DataFrame:
    rows = []
    failed = fit_results[fit_results["fit_status"].eq("failed")]
    low_conf = fit_results[fit_results["confidence"].eq("low")]
    with_printed = fit_results[pd.notna(fit_results["printed_IC50_nM"]) & fit_results["fit_status"].eq("success")].copy()
    with_printed["fold_disagreement"] = np.maximum(
        with_printed["fitted_vs_printed_ratio"].astype(float),
        1.0 / with_printed["fitted_vs_printed_ratio"].astype(float),
    )
    discordant = with_printed[with_printed["fold_disagreement"] > 2.0]

    def add(category: str, df: pd.DataFrame, status: str) -> None:
        if df.empty:
            rows.append({"category": category, "item": "none", "status": "none", "detail": ""})
            return
        for row in df.itertuples(index=False):
            detail = (
                f"{row.figure} {row.model} {row.drug} {row.fit_variant}; "
                f"fit={getattr(row, 'fitted_IC50_nM', math.nan):.6g} nM; "
                f"printed={getattr(row, 'printed_IC50_nM', math.nan):.6g} nM"
            )
            rows.append({"category": category, "item": f"{row.figure}:{row.model}:{row.drug}", "status": status, "detail": detail})

    add("failed_fits", failed, "failed")
    add("low_confidence_series", low_conf, "flagged")
    add("fitted_vs_printed_gt_2fold", discordant, "check")
    return pd.DataFrame(rows)


def pd_source_provenance() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "source": f"Wang et al. Cancer Res 2024; DOI {PD_PAPER_DOI}; PMCID {PD_PAPER_PMCID}",
                "data_role": "approximate digitized concentration-response points",
                "source_type": "PROMPT_INLINE_DIGITIZED_APPROXIMATE",
                "notes": (
                    "Numeric curve points remain approximate digitizations; Figure 2G matrix (100% AML patient "
                    "plasma), 48 h duration, and printed IC50 values were verified against the paper."
                ),
            },
            {
                "source": f"Wang et al. Figure 2G; DOI {PD_PAPER_DOI}; PMCID {PD_PAPER_PMCID}",
                "data_role": "paper-reported Figure 2G IC50 comparison anchors",
                "source_type": "WANG_2024_FIG2G_PRINTED_AUTHORITATIVE",
                "notes": "Paper-reported IC50 values are retained separately and never replaced by digitization-derived fits.",
            },
            {
                "source": "Eder PK model from pk_rcc",
                "data_role": "total plasma concentration for PK-PD exposure link",
                "source_type": "BORROWED_EXISTING_PK_MODEL",
                "notes": (
                    "Figure 2G permits an approximate matrix-matched total-to-total comparison without an extra "
                    "fu correction. This remains a descriptive cross-study bridge; no AML patient PK is invented."
                ),
            },
            {
                "source": f"Wang et al. Figure 2G; DOI {PD_PAPER_DOI}",
                "data_role": "PK-PD concentration-basis decision",
                "source_type": "VERIFIED_ASSAY_CONDITION_WITH_INFERRED_TOTAL_BASIS",
                "notes": FIG2G_NO_FU_JUSTIFICATION,
            },
        ]
    )


def build_pd_analysis_tables() -> dict[str, pd.DataFrame]:
    fit_results, points_and_fits, fit_grid = fit_all_series()
    return {
        "pd_source_points": source_points_table(),
        "pd_fit_results": fit_results,
        "pd_curve_points_and_fits": points_and_fits,
        "pd_growth_kill_parameters": growth_kill_parameter_table(fit_results),
        "pd_fit_curve_grid": fit_grid,
        "pd_potency_comparison": potency_comparison_table(fit_results),
        "pd_run_summary": pd_run_summary(fit_results),
        "pd_source_provenance": pd_source_provenance(),
    }


def ng_ml_to_nM_from_pk_rcc(conc_ng_ml: np.ndarray | pd.Series) -> np.ndarray:
    return np.asarray(conc_ng_ml, dtype=float) / FORETINIB_MW_G_MOL_FROM_PK_RCC * 1000.0


def validate_pkpd_unit_basis(
    *,
    pk_link_unit: str,
    pd_anchor_unit: str,
    clinical_pk_basis: str,
    pd_assay_basis: str,
    conversion_mw_g_mol: float,
) -> dict[str, str | float | bool]:
    """Fail fast if the Figure 2G clinical-PK bridge loses unit or basis consistency."""
    if pk_link_unit != "nM" or pd_anchor_unit != "nM":
        raise AssertionError("PK link concentrations and PD anchors must both be expressed in nM.")
    if "total plasma" not in clinical_pk_basis.lower():
        raise AssertionError("Clinical PK must be explicitly labeled as total plasma concentration.")
    if "total concentration" not in pd_assay_basis.lower() or "100% aml patient plasma" not in pd_assay_basis.lower():
        raise AssertionError("Figure 2G PD must be nominal total concentration in 100% AML patient plasma.")
    if not np.isclose(float(conversion_mw_g_mol), FORETINIB_FREE_BASE_MW_G_MOL, rtol=0.0, atol=1e-9):
        raise AssertionError("The ng/mL-to-nM conversion must use foretinib free-base MW from the PK configuration.")
    return {
        "unit_basis_guard_passed": True,
        "pk_input_unit": "ng/mL",
        "pk_link_unit": pk_link_unit,
        "pd_anchor_unit": pd_anchor_unit,
        "pk_conversion_mw_g_mol": float(conversion_mw_g_mol),
        "molecular_weight_basis": "foretinib free-base equivalent",
        "pd_anchor_mw_conversion": "not applicable; Figure 2G anchors are reported directly in nM",
    }


def pkpd_concentration_basis_metadata(figure: str) -> dict[str, str | bool]:
    """Describe whether total clinical PK is matrix-compatible with a PD assay."""
    if figure == "Fig2G":
        return {
            "clinical_pk_concentration_basis": CLINICAL_PK_CONCENTRATION_BASIS,
            "pd_assay_concentration_basis": FIG2G_ASSAY_CONCENTRATION_BASIS,
            "concentration_basis_label": FIG2G_CONCENTRATION_BASIS_LABEL,
            "pkpd_basis_status": FIG2G_PKPD_BASIS_STATUS,
            "free_fraction_correction_applied": FIG2G_FREE_FRACTION_CORRECTION_APPLIED,
            "free_fraction_decision": FIG2G_NO_FU_JUSTIFICATION,
        }
    if figure == "Fig2A":
        return {
            "clinical_pk_concentration_basis": CLINICAL_PK_CONCENTRATION_BASIS,
            "pd_assay_concentration_basis": FIG2A_ASSAY_CONCENTRATION_BASIS,
            "concentration_basis_label": "clinical total plasma nM versus standard-medium nominal nM; not matrix matched",
            "pkpd_basis_status": "NOT_MATRIX_MATCHED_TOTAL_TO_STANDARD_CULTURE",
            "free_fraction_correction_applied": False,
            "free_fraction_decision": (
                "Figure 2A used RPMI 1640 plus 10% FBS and is retained for in-vitro context, not as the "
                "clinical total-plasma potency anchor."
            ),
        }
    return {
        "clinical_pk_concentration_basis": CLINICAL_PK_CONCENTRATION_BASIS,
        "pd_assay_concentration_basis": "standard culture assay; not verified as 100% plasma",
        "concentration_basis_label": "clinical total plasma nM versus non-plasma-assay nominal nM; not matrix matched",
        "pkpd_basis_status": "NOT_MATRIX_MATCHED_TOTAL_TO_STANDARD_CULTURE",
        "free_fraction_correction_applied": False,
        "free_fraction_decision": (
            "No fu value is supplied; total clinical plasma versus standard-culture potency is not treated as "
            "a quantitatively basis-matched comparison."
        ),
    }


def pkpd_aml_exposure_coverage(pk_profiles: pd.DataFrame, fit_results: pd.DataFrame) -> pd.DataFrame:
    anchors = []
    foretinib = fit_results[fit_results["drug"].eq("Foretinib") & fit_results["fit_status"].eq("success")].copy()
    for row in foretinib.itertuples(index=False):
        basis = pkpd_concentration_basis_metadata(str(row.figure))
        anchors.append(
            {
                "anchor_id": f"{row.figure}:{row.model}:{row.endpoint}:{row.fit_variant}:fitted",
                "figure": row.figure,
                "model": row.model,
                "endpoint": row.endpoint,
                "anchor_type": "fitted_digitized_curve",
                "anchor_nM": float(row.fitted_IC50_nM),
                "confidence": row.confidence,
                **basis,
            }
        )
        if pd.notna(row.printed_IC50_nM):
            anchors.append(
                {
                    "anchor_id": f"{row.figure}:{row.model}:{row.endpoint}:printed",
                    "figure": row.figure,
                    "model": row.model,
                    "endpoint": row.endpoint,
                    "anchor_type": "printed_authoritative",
                    "anchor_nM": float(row.printed_IC50_nM),
                    "confidence": "paper_reported" if str(row.figure) == "Fig2G" else "prompt_reported",
                    **basis,
                }
            )
    anchor_df = pd.DataFrame(anchors).drop_duplicates("anchor_id")
    rows = []
    for scenario, profile in pk_profiles.groupby("scenario", sort=False):
        profile = profile.copy()
        conc_nM = ng_ml_to_nM_from_pk_rcc(profile["conc_ng_ml"])
        profile["conc_nM"] = conc_nM
        last_start = max(float(profile["day"].max()) - 1.0, 0.0)
        last = profile[profile["day"] >= last_start]
        last_nM = ng_ml_to_nM_from_pk_rcc(last["conc_ng_ml"])
        for anchor in anchor_df.itertuples(index=False):
            a = float(anchor.anchor_nM)
            if not np.isfinite(a) or a <= 0:
                continue
            rows.append(
                {
                    "scenario": scenario,
                    "anchor_id": anchor.anchor_id,
                    "figure": anchor.figure,
                    "model": anchor.model,
                    "endpoint": anchor.endpoint,
                    "anchor_type": anchor.anchor_type,
                    "anchor_nM": a,
                    "confidence": anchor.confidence,
                    "cmax_total_plasma_nM": float(np.max(conc_nM)),
                    "mean_last24_total_plasma_nM": float(np.mean(last_nM)),
                    "ctrough_last24_total_plasma_nM": float(np.min(last_nM)),
                    "cmax_over_anchor": float(np.max(conc_nM) / a),
                    "mean_last24_over_anchor": float(np.mean(last_nM) / a),
                    "ctrough_last24_over_anchor": float(np.min(last_nM) / a),
                    "pct_time_above_anchor": float(np.mean(conc_nM >= a) * 100.0),
                    "concentration_basis": anchor.concentration_basis_label,
                    "pkpd_basis_status": anchor.pkpd_basis_status,
                    "clinical_pk_concentration_basis": anchor.clinical_pk_concentration_basis,
                    "pd_assay_concentration_basis": anchor.pd_assay_concentration_basis,
                    "free_fraction_correction_applied": bool(anchor.free_fraction_correction_applied),
                    "free_fraction_decision": anchor.free_fraction_decision,
                    "source_type": "PKPD_LINK_DERIVED_FROM_EXISTING_PK_AND_INLINE_PD",
                    "model_note": (
                        "Coverage ratios are descriptive PK-PD overlays, not AML efficacy predictions. Figure 2G "
                        "is approximately matrix matched; other figures are retained with an explicit basis warning."
                    ),
                }
            )
    return pd.DataFrame(rows)


def pkpd_aml_projected_response(pk_profiles: pd.DataFrame, fit_results: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply foretinib PK profiles through a growth+kill ODE for viability endpoints."""
    foretinib = fit_results[
        fit_results["drug"].eq("Foretinib")
        & fit_results["fit_status"].eq("success")
        & fit_results["fit_variant"].eq("unweighted")
    ].copy()
    growth = estimate_aml_growth_rate_from_controls()
    timecourse_rows = []
    summary_rows = []
    for scenario, profile in pk_profiles.groupby("scenario", sort=False):
        profile = profile.copy().sort_values("day")
        conc_nM = ng_ml_to_nM_from_pk_rcc(profile["conc_ng_ml"])
        profile["conc_nM"] = conc_nM
        last_start = max(float(profile["day"].max()) - 1.0, 0.0)
        last_mask = profile["day"] >= last_start
        for _, fit_row in foretinib.iterrows():
            basis = pkpd_concentration_basis_metadata(str(fit_row["figure"]))
            direction = str(fit_row["direction"])
            endpoint = str(fit_row["endpoint"])
            is_viability_ode = "viability" in endpoint.lower() and direction == "decreasing"
            response_units = "percent viability" if "viability" in endpoint.lower() else "percent stabilization"
            if is_viability_ode:
                projection = simulate_cell_kill_projection(
                    profile["day"],
                    profile["conc_nM"],
                    fit_row,
                    k_g_per_day=float(growth["k_g_per_day"]),
                )
                pred = projection["projected_viability_pct"].to_numpy(dtype=float)
                instantaneous = projection["instantaneous_hill_response_pct"].to_numpy(dtype=float)
                kill_fraction = projection["hill_kill_fraction"].to_numpy(dtype=float)
                k_kill_t = projection["k_kill_t_per_day"].to_numpy(dtype=float)
                k_g = float(projection["k_g_per_day"].iloc[0])
                raw_k_g = float(projection["raw_k_g_per_day"].iloc[0])
                control_median = float(projection["control_response_median_pct"].iloc[0])
                k_kill_max = float(projection["k_kill_max_per_day"].iloc[0])
                raw_k_kill_max = float(projection["raw_k_kill_max_per_day"].iloc[0])
                carrying_capacity = float(projection["carrying_capacity_pct"].iloc[0])
                growth_source = str(projection["growth_rate_source"].iloc[0])
                kill_source = str(projection["kill_parameter_source"].iloc[0])
                source_type = "MODEL_PROJECTED_FROM_EXISTING_PK_AND_GROWTH_KILL_ODE"
                mechanistic_model = "JUSKO_STYLE_LOGISTIC_GROWTH_PLUS_HILL_DRIVEN_KILL"
                model_note = "Projected from growth+kill ODE; not observed AML efficacy. Hill fit supplies time-varying kill, not reversible viability."
            else:
                pred = predict_response_from_fit(profile["conc_nM"], fit_row)
                instantaneous = pred.copy()
                kill_fraction = np.full(len(pred), np.nan)
                k_kill_t = np.full(len(pred), np.nan)
                k_g = math.nan
                raw_k_g = math.nan
                control_median = math.nan
                k_kill_max = math.nan
                raw_k_kill_max = math.nan
                carrying_capacity = math.nan
                growth_source = "not_applicable_non_viability_endpoint"
                kill_source = "not_applicable_non_viability_endpoint"
                source_type = "MODEL_PROJECTED_FROM_EXISTING_PK_AND_FITTED_INLINE_PD"
                mechanistic_model = "DIRECT_HILL_LINK_FOR_NON_VIABILITY_ENDPOINT"
                model_note = "Direct fitted Hill projection retained for non-viability endpoint; not observed AML efficacy."

            last_pred = pred[np.asarray(last_mask, dtype=bool)]
            best_last24 = np.nanmin(last_pred) if direction == "decreasing" else np.nanmax(last_pred)
            worst_last24 = np.nanmax(last_pred) if direction == "decreasing" else np.nanmin(last_pred)
            peak_idx = int(np.nanargmax(profile["conc_nM"].to_numpy(dtype=float)))
            summary_rows.append(
                {
                    "scenario": scenario,
                    "figure": fit_row["figure"],
                    "model": fit_row["model"],
                    "mutation_or_condition": fit_row["mutation_or_condition"],
                    "endpoint": endpoint,
                    "fit_variant": fit_row["fit_variant"],
                    "response_direction": direction,
                    "confidence": fit_row["confidence"],
                    "fitted_IC50_or_EC50_nM": float(fit_row["fitted_IC50_nM"]),
                    "cmax_total_plasma_nM": float(np.nanmax(profile["conc_nM"])),
                    "mean_last24_total_plasma_nM": float(np.nanmean(profile.loc[last_mask, "conc_nM"])),
                    "predicted_response_at_cmax_pct": float(pred[peak_idx]),
                    "instantaneous_hill_response_at_cmax_pct": float(instantaneous[peak_idx]),
                    "mean_last24_predicted_response_pct": float(np.nanmean(last_pred)),
                    "best_last24_predicted_response_pct": float(best_last24),
                    "worst_last24_predicted_response_pct": float(worst_last24),
                    "response_units": response_units,
                    "concentration_basis": basis["concentration_basis_label"],
                    "pkpd_basis_status": basis["pkpd_basis_status"],
                    "clinical_pk_concentration_basis": basis["clinical_pk_concentration_basis"],
                    "pd_assay_concentration_basis": basis["pd_assay_concentration_basis"],
                    "free_fraction_correction_applied": basis["free_fraction_correction_applied"],
                    "free_fraction_decision": basis["free_fraction_decision"],
                    "mechanistic_model": mechanistic_model,
                    "k_g_per_day": k_g,
                    "raw_k_g_per_day": raw_k_g,
                    "control_response_median_pct": control_median,
                    "k_kill_max_per_day": k_kill_max,
                    "raw_k_kill_max_per_day": raw_k_kill_max,
                    "carrying_capacity_pct": carrying_capacity,
                    "growth_rate_source": growth_source,
                    "kill_parameter_source": kill_source,
                    "source_type": source_type,
                    "model_note": model_note,
                }
            )
            for point, response, direct_response, frac, k_t in zip(profile.itertuples(index=False), pred, instantaneous, kill_fraction, k_kill_t):
                timecourse_rows.append(
                    {
                        "scenario": scenario,
                        "day": float(point.day),
                        "conc_ng_ml": float(point.conc_ng_ml),
                        "conc_nM": float(point.conc_nM),
                        "figure": fit_row["figure"],
                        "model": fit_row["model"],
                        "mutation_or_condition": fit_row["mutation_or_condition"],
                        "endpoint": endpoint,
                        "fit_variant": fit_row["fit_variant"],
                        "response_direction": direction,
                        "confidence": fit_row["confidence"],
                        "fitted_IC50_or_EC50_nM": float(fit_row["fitted_IC50_nM"]),
                        "predicted_response_pct": float(response),
                        "instantaneous_hill_response_pct": float(direct_response),
                        "hill_kill_fraction": float(frac) if np.isfinite(frac) else math.nan,
                        "k_kill_t_per_day": float(k_t) if np.isfinite(k_t) else math.nan,
                        "response_units": response_units,
                        "concentration_basis": basis["concentration_basis_label"],
                        "pkpd_basis_status": basis["pkpd_basis_status"],
                        "clinical_pk_concentration_basis": basis["clinical_pk_concentration_basis"],
                        "pd_assay_concentration_basis": basis["pd_assay_concentration_basis"],
                        "free_fraction_correction_applied": basis["free_fraction_correction_applied"],
                        "free_fraction_decision": basis["free_fraction_decision"],
                        "mechanistic_model": mechanistic_model,
                        "k_g_per_day": k_g,
                        "k_kill_max_per_day": k_kill_max,
                        "carrying_capacity_pct": carrying_capacity,
                        "growth_rate_source": growth_source,
                        "kill_parameter_source": kill_source,
                        "source_type": source_type,
                        "model_note": model_note,
                    }
                )
    return pd.DataFrame(timecourse_rows), pd.DataFrame(summary_rows)