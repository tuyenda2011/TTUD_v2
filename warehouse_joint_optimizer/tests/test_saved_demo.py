import copy

import pytest

from warehouse_opt.demo_snapshot import validate_snapshot
from warehouse_opt.generator import generate
from warehouse_opt.models import InputError
from warehouse_opt.search import SearchConfig
from warehouse_opt.solver import solve


def test_saved_demo_rejects_modified_input_and_results():
    instance = generate(4, 7)
    snapshot = {"instance": instance.to_dict(), "results": {
        m: solve(instance, m, config=SearchConfig(seconds=0, iterations=2)) for m in ("B0", "VNS")}}
    validate_snapshot(snapshot)
    tampered = copy.deepcopy(snapshot)
    tampered["instance"]["orders"][0]["due"] += 1
    with pytest.raises(InputError):
        validate_snapshot(tampered)
    tampered = copy.deepcopy(snapshot)
    tampered["results"]["VNS"]["metrics"]["distance"] += 1
    with pytest.raises(InputError):
        validate_snapshot(tampered)
