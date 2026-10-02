"""Declared soft-deadline objectives; weights are preferences, not guarantees."""
from .models import InputError

WEIGHT_PROFILES = {
    "balanced": (1 / 3, 1 / 3, 1 / 3),
    "distance": (.6, .2, .2),
    "makespan": (.2, .6, .2),
    "tardiness": (.2, .2, .6),
}


def profile_weights(name="balanced"):
    if not isinstance(name, str) or name not in WEIGHT_PROFILES:
        raise InputError(f"Unknown objective profile: {name}; choose {tuple(WEIGHT_PROFILES)}")
    return WEIGHT_PROFILES[name]
