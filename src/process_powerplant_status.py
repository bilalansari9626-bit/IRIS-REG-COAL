
"""Extract official coal power plant status records from BNetzA CSV."""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/opportunities/Kraftwerksliste_CSV.csv"
OUTPUT = ROOT / "data/opportunities/coal_powerplant_status.csv"
REPORT = ROOT / "reports/coal_powerplant_status.json"

df = pd.read_csv(
    SOURCE,
    sep=";",
    encoding="cp1252",
    header=7,
    dtype=str,
)

coal = df[
    df["Energietraeger"].isin(["Braunkohle", "Steinkohle"])
].copy()

if coal.empty:
    raise ValueError("No coal power plant records found")

missing_ids = coal["EinheitMastrNummer"].isna().sum()

valid_ids = coal["EinheitMastrNummer"].dropna()

duplicate_ids = valid_ids.duplicated().sum()

print(f"Missing identifiers: {missing_ids}")
print(f"Duplicate non-empty identifiers: {duplicate_ids}")

columns = [
    "EinheitMastrNummer",
    "Anlagenbetreiber",
    "Anzeigename",
    "Bundesland",
    "Energietraeger",
    "Kraftwerksstatus",
    "Jahr_Inbetriebnahme",
    "Jahr_Stilllegung**",
    "Nettonennleistung_MW",
]

coal[columns].to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8-sig",
)

report = {
    "source": "Bundesnetzagentur Kraftwerksliste",
    "source_file": SOURCE.name,
    "total_source_records": len(df),
    "coal_records": len(coal),
    "missing_identifiers": int(missing_ids),
    "duplicate_identifiers": int(duplicate_ids),
    "fuel_counts": coal["Energietraeger"].value_counts().to_dict(),
    "status_counts": coal["Kraftwerksstatus"].value_counts().to_dict(),
    "limitations": [
        "Source CSV does not include geographic coordinates.",
        "Plant locations cannot be assigned to coal districts.",
        "This is a national coal-status dataset, not a spatial overlay.",
    ],
}

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(
    json.dumps(report, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print(f"SUCCESS: {len(coal)} coal power plant records")
print(f"Output: {OUTPUT}")
print(f"Report: {REPORT}")
