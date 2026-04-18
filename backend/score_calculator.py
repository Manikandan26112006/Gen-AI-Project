"""
KPI Score Calculator – weighted formula as per TFRS
"""

# Weights (must sum to 100)
WEIGHTS = {
    "publications":              10,   # total publications
    "scie_scopus":               20,   # SCIE/Scopus indexed
    "conferences":                5,   # conference papers
    "books":                      5,   # books / book chapters
    "fdp_sttp":                   8,   # FDP / STTP attended
    "nptel":                      5,   # NPTEL certifications
    "workshops_organized":        5,   # workshops conducted
    "industrial_training":        5,   # industrial training
    "consultancy_projects":      10,   # consultancy
    "research_funding":          15,   # research grants (in lakhs or count)
    "patents":                   10,   # IPR / patents
    "institutional_activities":   2,   # institutional contribution (max 10)
    "feedback_score":             0,   # used separately below
}

# Max expected values per KPI (for normalisation to 0-100)
MAX_VALUES = {
    "publications":             15,
    "scie_scopus":              10,
    "conferences":              10,
    "books":                     5,
    "fdp_sttp":                  8,
    "nptel":                     6,
    "workshops_organized":       5,
    "industrial_training":       4,
    "consultancy_projects":      6,
    "research_funding":          6,
    "patents":                   5,
    "institutional_activities": 10,
    "feedback_score":            5,
}


def normalise(value, max_val):
    """Clamp value between 0-max_val then scale to 0-100."""
    return min(max(float(value), 0), max_val) / max_val * 100


def calculate_score(row) -> float:
    """
    Calculate weighted performance score (0-100).
    `row` can be a pandas Series or a dict-like with KPI fields.
    """
    total_weight = 0
    weighted_sum = 0.0

    for kpi, weight in WEIGHTS.items():
        if weight == 0:
            continue
        val = row.get(kpi, 0) if hasattr(row, 'get') else getattr(row, kpi, 0)
        norm = normalise(val, MAX_VALUES[kpi])
        weighted_sum += norm * weight
        total_weight  += weight

    # Feedback score contributes 5 bonus points (out of 100)
    fb = row.get("feedback_score", 0) if hasattr(row, 'get') else getattr(row, "feedback_score", 0)
    fb_bonus = (float(fb) / MAX_VALUES["feedback_score"]) * 5

    raw_score = (weighted_sum / total_weight) + fb_bonus    # 0-105
    return round(min(raw_score, 100), 2)


def classify_score(score: float) -> str:
    """Return performance level label."""
    if score >= 85:
        return "Excellent"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Average"
    else:
        return "Needs Improvement"


def get_recommendations(row) -> list[str]:
    """Return a list of targeted recommendation strings for the given KPI row."""
    recs = []
    if row.get("publications", 0) < 3:
        recs.append("Increase research publications – aim for at least 3 per year.")
    if row.get("scie_scopus", 0) < 2:
        recs.append("Target SCIE/Scopus indexed journals to boost research visibility.")
    if row.get("fdp_sttp", 0) < 2:
        recs.append("Attend at least 2 FDP/STTP programmes annually.")
    if row.get("nptel", 0) < 1:
        recs.append("Complete at least 1 NPTEL certification to enhance academic profile.")
    if row.get("research_funding", 0) < 1:
        recs.append("Apply for funded research grants (DST, SERB, AICTE, etc.).")
    if row.get("patents", 0) < 1:
        recs.append("Explore filing patents or IPR disclosures for research outcomes.")
    if row.get("consultancy_projects", 0) < 1:
        recs.append("Engage in at least 1 consultancy/industrial project per year.")
    if row.get("workshops_organized", 0) < 1:
        recs.append("Organise a workshop or symposium to strengthen institutional role.")
    if row.get("industrial_training", 0) < 1:
        recs.append("Undertake industrial training to bridge academia-industry gap.")
    if row.get("feedback_score", 0) < 4.0:
        recs.append("Focus on teaching quality to improve student feedback score.")
    if not recs:
        recs.append("Excellent work! Maintain the current performance trajectory.")
    return recs