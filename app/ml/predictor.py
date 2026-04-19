import pickle
import numpy as np
from pathlib import Path

MODEL_PATH = Path("data/model.pkl")
FEATURES = [
    "attendance_rate",
    "assignment_completion",
    "avg_grade",
    "forum_posts",
    "time_on_platform",
    "late_submissions",
]


def _generate_training_data():
    rng = np.random.default_rng(42)
    n = 500

    attendance_rate = rng.beta(5, 2, n)
    assignment_completion = rng.beta(5, 2, n)
    avg_grade = rng.normal(70, 15, n).clip(0, 100)
    forum_posts = rng.poisson(8, n).clip(0, 50)
    time_on_platform = rng.exponential(12, n).clip(0, 40)
    late_submissions = rng.poisson(3, n).clip(0, 20)

    risk_score = (
        (1 - attendance_rate) * 0.25
        + (1 - assignment_completion) * 0.25
        + (1 - avg_grade / 100) * 0.2
        + (late_submissions / 20) * 0.15
        + (1 - time_on_platform / 40) * 0.15
    )
    at_risk = (risk_score > 0.45).astype(int)

    X = np.column_stack(
        [attendance_rate, assignment_completion, avg_grade, forum_posts, time_on_platform, late_submissions]
    )
    return X, at_risk


def _train_and_save():
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split

    X, y = _generate_training_data()
    X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    MODEL_PATH.parent.mkdir(exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    return model


def _load_model():
    if not MODEL_PATH.exists():
        return _train_and_save()
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


_model = None


def get_model():
    global _model
    if _model is None:
        _model = _load_model()
    return _model


def predict(student_data: list) -> list:
    model = get_model()
    importances = model.feature_importances_
    top_indices = np.argsort(importances)[::-1][:3]
    top_risk_factors = [FEATURES[i] for i in top_indices]

    results = []
    for student in student_data:
        X = np.array([[
            student["attendance_rate"],
            student["assignment_completion"],
            student["avg_grade"],
            student["forum_posts"],
            student["time_on_platform"],
            student["late_submissions"],
        ]])

        proba = model.predict_proba(X)[0]
        risk_score = float(proba[1]) if len(proba) > 1 else float(proba[0])

        if risk_score < 0.4:
            risk_level = "low"
        elif risk_score <= 0.7:
            risk_level = "medium"
        else:
            risk_level = "high"

        results.append({
            "student_id": student["student_id"],
            "risk_score": round(risk_score, 3),
            "risk_level": risk_level,
            "top_risk_factors": top_risk_factors,
        })

    return results
