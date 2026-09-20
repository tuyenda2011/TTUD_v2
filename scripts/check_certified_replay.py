"""Exercise the real Canvas replay against certified exact solutions in Edge."""
import argparse
import json
import math
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright

from demo.simulation import build_simulation_data, render_simulation
from src.models import read_instance, write_json
from src.validator import validate_solution


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    reports, errors = [], []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        for path in sorted((args.study / "exact/raw").glob("*-EXACT.json")):
            result = json.loads(path.read_text(encoding="utf-8"))
            if result["method"] != "EXACT":
                continue  # Windows glob also matches the lower-case route-exact suffix.
            assert result["certified_optimal"], path
            instance = read_instance(args.study / "exact/instances" / f"{result['instance']}.json")
            assert not validate_solution(instance, result)
            data = build_simulation_data(instance, result)
            # Capture the actual HTML passed to Streamlit; no replacement of solver or renderer.
            with patch("demo.simulation.components.html") as output:
                render_simulation(instance, result)
                html = output.call_args.args[0]
            (args.output / f"{instance.name}.html").write_text(html, encoding="utf-8")
            page = browser.new_page(viewport={"width": 1100, "height": 750})
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.set_content(html)
            page.locator("#resetBtn").click()
            assert page.evaluate("simTime === 0 && !isPlaying")
            assert page.evaluate("simData.makespan") == result["metrics"]["makespan"]
            samples = 0
            for picker in data["pickers"]:
                for segment in picker["segments"]:
                    duration = segment["t_end"] - segment["t_start"]
                    if duration < 0.0001:
                        continue
                    state = page.evaluate("([id,t]) => getPickerState(simData.pickers.find(p=>p.id===id),t)",
                                          [picker["id"], (segment["t_start"] + segment["t_end"]) / 2])
                    assert state["state"] == segment["state"]
                    assert state["load"] == segment["load"]
                    for axis in ("x", "y"):
                        assert math.isclose(state[axis], (segment[axis + "1"] + segment[axis + "2"]) / 2, abs_tol=1e-8)
                    samples += 1
            page.locator("#playBtn").click()
            page.wait_for_function("simTime > 0")
            page.locator("#playBtn").click()
            assert not page.evaluate("isPlaying")
            page.locator("#timelineSlider").evaluate("el => { el.value=el.max; el.dispatchEvent(new Event('input')); }")
            assert page.evaluate("simData.pickers.every(p=>getPickerState(p,simTime).state==='idle')")
            page.locator("#zoomInBtn").click()
            assert page.evaluate("zoomFactor > 1")
            page.locator("#zoomResetBtn").click()
            assert page.locator(".controls-bar").evaluate("el => el.scrollWidth <= el.clientWidth")
            page.screenshot(path=str(args.output / f"{instance.name}.png"))
            page.set_viewport_size({"width": 390, "height": 750})
            assert page.locator(".controls-bar").evaluate("el => el.scrollWidth <= el.clientWidth")
            assert page.locator("#timeBadge").evaluate("el => el.getBoundingClientRect().right <= el.parentElement.getBoundingClientRect().right + 1")
            page.screenshot(path=str(args.output / f"{instance.name}-mobile.png"))
            assert not errors, errors
            reports.append({"instance": instance.name, "certified_optimal": True, "samples": samples,
                            "controls": ["reset", "play", "pause", "seek_end", "zoom"],
                            "viewports": [1100, 390], "page_errors": []})
            page.close()
        browser.close()
    assert reports, "No certified exact results found"
    write_json(args.output / "verification.json", {"cases": reports, "page_errors": errors})
    print(f"Verified {len(reports)} certified replays, {sum(r['samples'] for r in reports)} segment samples")


if __name__ == "__main__":
    main()
