"""Validate saved demo snapshots before displaying any stored results."""
from .models import InputError, Instance
from .solver import fingerprint
from .validator import validate_solution


def validate_snapshot(snapshot):
    if not isinstance(snapshot, dict) or "instance" not in snapshot:
        raise InputError("Saved demo must be an object containing instance and results")
    if not isinstance(snapshot.get("results"), dict):
        raise InputError("Saved demo results must be an object")
    instance = Instance.from_dict(snapshot["instance"])
    if "B0" not in snapshot["results"]:
        raise InputError("Saved demo requires B0")
    for method, result in snapshot["results"].items():
        if not isinstance(result, dict):
            raise InputError(f"Saved demo result {method} must be an object")
    instance_hash = fingerprint(instance)
    for method, result in snapshot["results"].items():
        errors = validate_solution(instance, result)
        if result.get("instance_sha256") != instance_hash:
            errors.append("Instance fingerprint mismatch")
        if result.get("method") != method:
            errors.append("Method mismatch")
        if result.get("objective_config") != snapshot["results"]["B0"].get("objective_config"):
            errors.append("Objective configuration mismatch")
        if errors:
            raise InputError("; ".join(errors))
    return snapshot
