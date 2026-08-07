PHYSICAL_ASSESSMENT_FIELDS = (
    "weight_kg",
    "body_fat_percentage",
    "chest_cm",
    "waist_cm",
    "hips_cm",
    "left_arm_cm",
    "right_arm_cm",
    "left_thigh_cm",
    "right_thigh_cm",
    "resting_heart_rate",
)


def at_least_one_physical_assessment_required(values: dict) -> bool:
    """True if at least one body-measurement field in `values` is populated."""
    return any(values.get(field) is not None for field in PHYSICAL_ASSESSMENT_FIELDS)
