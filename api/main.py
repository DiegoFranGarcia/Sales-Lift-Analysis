# api/main.py
"""
FastAPI backend for the Sales-Lift-Analysis narrative app.

Serves precomputed results only - nothing is estimated at request time. All
figures come from files written by the analysis scripts, so the app cannot
drift from the committed results.

  outputs/headline.json           src/build_headline.py
  outputs/spec_curve.csv          src/spec_curve.py
  outputs/placebo_intime.csv      src/placebos/placebo_intime.py
  outputs/cs_event_study_boot.csv src/pretrends.py
  outputs/loo_cohort.csv          src/loo.py
"""
import json
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

OUT = Path("outputs")

app = FastAPI(title="Sales Lift Analysis", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

_cache = {}


def load(name, loader):
    if name not in _cache:
        path = OUT / name
        if not path.exists():
            raise HTTPException(503, f"{name} not built yet")
        _cache[name] = loader(path)
    return _cache[name]


def csv(path):
    return pd.read_csv(path).replace({float("nan"): None}).to_dict("records")


@app.get("/api/headline")
def headline():
    """The estimate ladder, diagnostics, and §12 condition status."""
    return load("headline.json", lambda p: json.loads(p.read_text()))


@app.get("/api/spec-curve")
def spec_curve():
    """
    128 specifications. The frontend filters client-side, so the whole grid
    ships at once - it is a few hundred rows.
    """
    rows = load("spec_curve.csv", csv)
    branches = ["grain", "closure_rule", "gapped", "pre_min",
                "outcome", "control"]
    return {
        "rows": rows,
        "branches": {b: sorted({r[b] for r in rows}, key=str) for b in branches},
    }


@app.get("/api/placebo-intime")
def placebo_intime():
    """500 in-time placebo draws, for the null-distribution histogram."""
    rows = load("placebo_intime.csv", csv)
    return {"draws": [r["att"] for r in rows]}


@app.get("/api/event-study")
def event_study():
    """
    Event-study coefficients with pointwise CIs and uniform bands.

    Horizons beyond about -60 rest on 1-9 of 15 cohorts, so the `n` column
    (contributing cohorts) ships with each row and the frontend dims the
    thin ones rather than hiding them.
    """
    rows = load("cs_event_study_boot.csv", csv)
    keep = ["event_time", "att", "se", "conf_int_lower", "conf_int_upper",
            "cband_lower", "cband_upper", "n", "is_reference"]
    return {"rows": [{k: r.get(k) for k in keep if k in r} for r in rows]}


@app.get("/api/leave-one-out")
def leave_one_out():
    """Leave-one-cohort-out estimates, sorted by impact."""
    rows = load("loo_cohort.csv", csv)
    return {"rows": sorted(rows, key=lambda r: r["delta"])}


@app.get("/api/health")
def health():
    """Which artifacts are present, so a missing file is obvious at a glance."""
    files = ["headline.json", "spec_curve.csv", "placebo_intime.csv",
             "cs_event_study_boot.csv", "loo_cohort.csv"]
    return {f: (OUT / f).exists() for f in files}