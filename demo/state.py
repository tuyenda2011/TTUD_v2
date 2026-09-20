"""Input preparation and run lifecycle, independent of Streamlit."""
import hashlib
import json

from src.generator import MAP_SCENARIOS, generate_scenario
from src.models import InputError, Instance, read_instance
from src.search import SearchConfig
from src.solver import solve

SYNTHETIC = "Dữ liệu tổng hợp — chỉ kiểm thử"
KRIS = "Kris — benchmark tác giả"
UPLOAD = "JSON tải lên"


def upload_digest(content):
    return hashlib.sha256(content).hexdigest() if content is not None else None


def prepare_instance(draft, root, content=None):
    if draft["source"] == SYNTHETIC:
        scenario_key = draft.get("scenario", "single_block")
        if scenario_key not in MAP_SCENARIOS:
            raise InputError(f"Unknown scenario {scenario_key}; choose {tuple(MAP_SCENARIOS)}")
        scen_cfg = MAP_SCENARIOS[scenario_key]
        return generate_scenario(
            scenario_key,
            seed=draft.get("seed", 42),
            n=draft.get("orders", scen_cfg["n"]),
            pickers=draft.get("pickers", scen_cfg["pickers"]),
            capacity=draft.get("capacity", scen_cfg["capacity"]),
            tightness=draft.get("tightness", scen_cfg["tightness"]),
        )
    if draft["source"] == KRIS:
        if not draft.get("file"):
            raise InputError("Chưa có dữ liệu Kris. Chọn dữ liệu tổng hợp hoặc chuẩn bị catalog Kris.")
        path = (root / draft["file"]).resolve()
        if not path.is_relative_to((root / "data/processed").resolve()):
            raise InputError("Đường dẫn Kris không hợp lệ.")
        return read_instance(path)
    if draft["source"] == UPLOAD:
        if content is None:
            raise InputError("Chọn file JSON chứa kho và đơn hàng trước khi chạy.")
        return Instance.from_dict(json.loads(content.decode("utf-8-sig")))
    raise InputError("Nguồn dữ liệu không được hỗ trợ.")


def methods_for(draft):
    methods = ["B0", "B1", "B2", "B3", "LNS", "ALNS"] if draft["comparison"] else ["B0", "ALNS"]
    return methods + (["VNS"] if draft["vns"] else [])


def start_run(state):
    state["run_status"] = "running"
    state.pop("run_error", None)
    state.pop("snapshot", None)
    for key in ("result_method", "route_picker", "route_batch"):
        state.pop(key, None)


def fail_run(state, error):
    state["run_status"] = "error"
    state["run_error"] = str(error)
    state.pop("snapshot", None)


def finish_run(state, snapshot):
    state["snapshot"] = snapshot
    state["run_status"] = "success"
    state.pop("run_error", None)


def is_stale(snapshot, draft):
    return snapshot.get("draft") != draft


def run_scenario(instance, draft, progress=None):
    methods = methods_for(draft)
    results = {}
    for index, method in enumerate(methods):
        if progress:
            progress(index / len(methods), f"Đang chạy {method} · {index + 1}/{len(methods)}")
        results[method] = solve(instance, method, draft["seed"],
                                SearchConfig(seconds=draft["seconds"], iterations=2000))
    return {"instance": instance.to_dict(), "results": results, "draft": dict(draft),
            "seed": draft["seed"], "budget": draft["seconds"], "saved_playback": False}


def improvement(value, baseline):
    return None if baseline == 0 else 100 * (baseline - value) / baseline
