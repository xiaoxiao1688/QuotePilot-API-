from __future__ import annotations

from pathlib import Path
import random

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier


LABELS = ["low", "medium", "high"]


def build_dataset(sample_count: int = 1800) -> tuple[np.ndarray, np.ndarray]:
    random.seed(42)
    rows: list[list[float]] = []
    labels: list[int] = []

    for _ in range(sample_count):
        relative_total_cost = random.uniform(0.72, 1.35)
        average_lead_time = random.uniform(2, 28)
        parse_confidence = random.uniform(0.45, 0.99)
        shipping_ratio = random.uniform(0.0, 0.2)
        item_count = random.randint(1, 12)
        missing_lead_time = 1.0 if random.random() < 0.15 else 0.0

        risk_points = 0
        if relative_total_cost < 0.88 or relative_total_cost > 1.22:
            risk_points += 2
        elif relative_total_cost < 0.94 or relative_total_cost > 1.12:
            risk_points += 1

        if average_lead_time > 18:
            risk_points += 2
        elif average_lead_time > 10:
            risk_points += 1

        if parse_confidence < 0.65:
            risk_points += 2
        elif parse_confidence < 0.8:
            risk_points += 1

        if shipping_ratio > 0.14:
            risk_points += 2
        elif shipping_ratio > 0.08:
            risk_points += 1

        if missing_lead_time > 0:
            risk_points += 2

        if item_count > 8:
            risk_points += 1

        risk_points += random.choice([0, 0, 0, 1])

        if risk_points <= 2:
            label = 0
        elif risk_points <= 5:
            label = 1
        else:
            label = 2

        rows.append([
            relative_total_cost,
            average_lead_time,
            parse_confidence,
            shipping_ratio,
            float(item_count),
            missing_lead_time,
        ])
        labels.append(label)

    return np.array(rows, dtype=float), np.array(labels, dtype=int)


def main() -> None:
    features, labels = build_dataset()
    model = RandomForestClassifier(
        n_estimators=180,
        max_depth=8,
        random_state=42,
    )
    model.fit(features, labels)

    output_dir = Path("models")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "quote_risk_model.joblib"
    joblib.dump(
        {
            "model": model,
            "labels": LABELS,
            "features": [
                "relative_total_cost",
                "average_lead_time_days",
                "parse_confidence",
                "shipping_ratio",
                "item_count",
                "missing_lead_time",
            ],
        },
        output_path,
    )
    print(output_path)


if __name__ == "__main__":
    main()

