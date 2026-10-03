"""Browser acceptance test. Requires playwright and installed Microsoft Edge."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from playwright.sync_api import expect, sync_playwright

from src.demo_snapshot import validate_snapshot
from src.evaluation_figures import MAP_LABELS
from src.models import Instance
from src.generator import generate
from src.validator import validate_solution


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8503")
    parser.add_argument("--output", default="results/ui_audit")
    args = parser.parse_args()
    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=True)
    checks, errors = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(args.url)
        expect(page.locator(".st-key-run").get_by_role("button")).to_be_visible(timeout=45000)
        expect(page.locator('[data-testid="stSkeleton"]')).to_have_count(0)
        page.screenshot(path=str(output / "after-desktop-empty.png"), full_page=True)

        def select(key, value):
            settled()
            widget = page.locator(f".st-key-{key}")
            control = widget.get_by_role("combobox")
            control.press("Escape")
            widget.get_by_role("button", name="Open", exact=True).click()
            option = page.get_by_role("option", name=value, exact=True)
            expect(option).to_be_visible(timeout=15000)
            option.click()
            expect(control).to_have_value(value)
            settled()

        def settled():
            expect(page.get_by_test_id("stStatusWidget")).to_have_count(0, timeout=45000)
            expect(page.get_by_test_id("stSkeleton")).to_have_count(0)

        def open_downloads():
            if not page.get_by_role("button", name="Tải toàn bộ lần chạy (JSON)", exact=True).is_visible():
                page.get_by_text("Tải kết quả", exact=True).click()

        def run(instance_name):
            page.locator(".st-key-run").get_by_role("button").click()
            expect(page.get_by_text("Cấu hình bên trái chưa được áp dụng", exact=False)).to_have_count(0, timeout=45000)
            expect(page.locator(".st-key-result_method").get_by_role("combobox")).to_be_visible(timeout=45000)
            settled()
            page.get_by_role("tab", name="Tổng quan", exact=True).click()
            expect(page.get_by_text("Kết quả của phương án", exact=True)).to_be_visible(timeout=45000)
            expect(page.get_by_test_id("stMetric")).to_have_count(3)
            expect(page.get_by_text("Cấu hình bên trái chưa được áp dụng", exact=False)).to_have_count(0)
            open_downloads()
            with page.expect_download() as event:
                page.get_by_role("button", name="Tải toàn bộ lần chạy (JSON)", exact=True).click()
            destination = output / f"{instance_name}-run-snapshot.json"
            event.value.save_as(destination)
            evidence = validate_snapshot(json.loads(destination.read_text(encoding="utf-8")))
            assert evidence["instance"]["name"] == instance_name
            settled()

        run("synthetic-n10-seed42")
        page.screenshot(path=str(output / "after-desktop-results.png"), full_page=True)
        page.get_by_role("tab", name="Tuyến và lịch", exact=True).click()
        expect(page.get_by_text("Lịch làm việc", exact=True)).to_be_visible()
        expect(page.locator('img:visible')).to_have_count(2)
        page.wait_for_function("[...document.images].every(img => img.complete && img.naturalWidth > 0)")
        page.screenshot(path=str(output / "after-desktop-route.png"), full_page=True)
        page.locator('img:visible').first.screenshot(path=str(output / "route-10.png"))
        select("route_picker", "Nhân viên 2")
        expect(page.get_by_text("Lịch làm việc", exact=True)).to_be_visible()
        assert page.locator('[data-testid="stException"]').count() == 0
        checks.append("default run and picker/batch filters")

        open_downloads()
        with page.expect_download() as download_info:
            page.get_by_role("button", name="Tải toàn bộ lần chạy (JSON)", exact=True).click()
        snapshot_path = output / "downloaded-snapshot.json"
        download_info.value.save_as(snapshot_path)
        snapshot = validate_snapshot(json.loads(snapshot_path.read_text(encoding="utf-8")))
        assert set(snapshot["results"]) == {"B0", "ALNS"}
        with page.expect_download() as download_info:
            page.get_by_role("button", name="Tải phương án (JSON)", exact=True).click()
        result_path = output / "downloaded-solution.json"
        download_info.value.save_as(result_path)
        assert not validate_solution(Instance.from_dict(snapshot["instance"]), json.loads(result_path.read_text(encoding="utf-8")))
        checks.append("download snapshot and solution; independent validation")

        page.get_by_text("Nâng cao", exact=True).click()
        select("objective_profile", "Giảm tổng độ trễ")
        expect(page.get_by_text("Cấu hình bên trái chưa được áp dụng", exact=False)).to_be_visible()
        page.locator(".st-key-run").get_by_role("button").click()
        expect(page.get_by_text("Cấu hình bên trái chưa được áp dụng", exact=False)).to_have_count(0, timeout=45000)
        expect(page.locator(".st-key-result_method").get_by_role("combobox")).to_be_visible(timeout=45000)
        settled()
        page.get_by_role("tab", name="Đánh giá", exact=True).click()
        page.get_by_text("Chỉ số đầy đủ của lần chạy", exact=True).click()
        weights = page.get_by_text("Trọng số cho quãng đường / thời gian hoàn tất / tổng độ trễ: 0.200 / 0.200 / 0.600.", exact=False)
        expect(weights).to_be_visible()
        open_downloads()
        with page.expect_download() as download_info:
            page.get_by_role("button", name="Tải toàn bộ lần chạy (JSON)", exact=True).click()
        weighted_path = output / "weighted-snapshot.json"
        download_info.value.save_as(weighted_path)
        weighted = validate_snapshot(json.loads(weighted_path.read_text(encoding="utf-8")))
        assert all(tuple(r["objective_config"]["weights"]) == (.2, .2, .6) for r in weighted["results"].values())
        settled()
        weights.scroll_into_view_if_needed()
        page.screenshot(path=str(output / "after-weighted-results.png"), full_page=True)
        checks.append("objective preference marks draft stale; rerun and export keep selected weights")

        page.locator(".st-key-comparison").locator("label").click()
        expect(page.locator(".st-key-comparison").get_by_role("checkbox")).to_be_checked()
        expect(page.get_by_text("Cấu hình bên trái chưa được áp dụng", exact=False)).to_be_visible()
        run("synthetic-n10-seed42")
        open_downloads()
        with page.expect_download() as download_info:
            page.get_by_role("button", name="Tải toàn bộ lần chạy (JSON)", exact=True).click()
        comparison_path = output / "comparison-snapshot.json"
        download_info.value.save_as(comparison_path)
        comparison = validate_snapshot(json.loads(comparison_path.read_text(encoding="utf-8")))
        assert set(comparison["results"]) == {"B0", "B2", "LNS", "ALNS", "VNS"}
        assert all(tuple(r["objective_config"]["weights"]) == (.2, .2, .6)
                   for r in comparison["results"].values())
        page.screenshot(path=str(output / "after-comparison-results.png"), full_page=True)
        checks.append("comparison runs all five algorithms with selected objective weights")

        page.locator(".st-key-orders").get_by_role("spinbutton").fill("30")
        page.locator(".st-key-orders").get_by_role("spinbutton").press("Enter")
        expect(page.get_by_text("Cấu hình bên trái chưa được áp dụng", exact=False)).to_be_visible()
        run("synthetic-n30-seed42")
        page.get_by_role("tab", name="Tuyến và lịch", exact=True).click()
        expect(page.locator('img:visible')).to_have_count(2)
        page.wait_for_function("[...document.images].every(img => img.complete && img.naturalWidth > 0)")
        page.screenshot(path=str(output / "after-route-30.png"), full_page=True)
        page.locator('img:visible').first.screenshot(path=str(output / "route-30.png"))
        checks.append("changed draft marked stale; 30-order rerun")

        page.locator(".st-key-reset_map_defaults").get_by_role("button").click()
        expect(page.locator(".st-key-orders").get_by_role("spinbutton")).to_have_value("10")
        expect(page.get_by_text("Cấu hình bên trái chưa được áp dụng", exact=False)).to_be_visible()
        assert page.get_by_test_id("stException").count() == 0
        checks.append("reset map defaults after changing inputs preserves old result and marks it stale")

        select("scenario", MAP_LABELS["double_block"])
        run("double_block-synthetic-n30-seed42")
        page.get_by_role("tab", name="Mô phỏng", exact=True).click()
        expect(page.frame_locator("iframe").locator("#simCanvas")).to_be_visible()
        assert page.get_by_test_id("stException").count() == 0
        page.screenshot(path=str(output / "after-double-block.png"), full_page=True)
        checks.append("double-block scenario and replay tab")

        select("source", "Tải dữ liệu JSON")
        expect(page.locator(".st-key-orders")).to_have_count(0)
        upload = page.locator('.st-key-upload input[type="file"]')
        upload.set_input_files({"name": "invalid.json", "mimeType": "application/json", "buffer": b"{}"})
        expect(page.get_by_role("button", name="Remove invalid.json", exact=True)).to_be_visible()
        settled()
        page.locator(".st-key-run").get_by_role("button").click()
        expect(page.get_by_text("Không thể chạy thuật toán.", exact=False)).to_be_visible(timeout=30000)
        expect(page.get_by_test_id("stMetric")).to_have_count(0)
        settled()
        page.get_by_role("button", name="Remove invalid.json", exact=True).click()
        expect(page.get_by_role("button", name="Remove invalid.json", exact=True)).to_have_count(0)
        tiny = generate(n=4, seed=42)
        upload.set_input_files({"name": "tiny_4.json", "mimeType": "application/json",
                               "buffer": json.dumps(tiny.to_dict()).encode("utf-8")})
        expect(page.get_by_role("button", name="Remove tiny_4.json", exact=True)).to_be_visible()
        settled()
        run(tiny.name)
        checks.append("JSON invalid clears old result; valid upload runs")

        select("source", "Bộ dữ liệu Kris")
        expect(page.locator(".st-key-kris_file")).to_be_visible()
        run("Kris-instances_106_1")
        checks.append("Kris dataset runs")

        laptop = browser.new_page(viewport={"width": 1366, "height": 768})
        laptop.on("pageerror", lambda error: errors.append(str(error)))
        laptop.goto(args.url)
        run_button = laptop.get_by_test_id("stSidebar").locator(".st-key-run").get_by_role("button")
        expect(run_button).to_be_visible(timeout=45000)
        expect(run_button).to_be_in_viewport()
        laptop.screenshot(path=str(output / "after-laptop-empty.png"), full_page=True)
        run_button.click()
        expect(laptop.locator(".st-key-result_method").get_by_role("combobox")).to_be_visible(timeout=45000)
        expect(laptop.get_by_test_id("stMetric")).to_have_count(3)
        expect(laptop.get_by_test_id("stStatusWidget")).to_have_count(0, timeout=45000)
        laptop.get_by_role("tab", name="Mô phỏng", exact=True).click()
        simulation = laptop.frame_locator("iframe")
        expect(simulation.locator("#simCanvas")).to_be_visible(timeout=45000)
        assert simulation.locator("html").evaluate(
            "el => el.scrollWidth <= window.innerWidth + 1 && el.scrollHeight <= window.innerHeight + 1"
        ), "simulation iframe overflow"
        assert laptop.locator("iframe").evaluate("el => { const frame = el.getBoundingClientRect(); "
                                                "const main = el.closest('[data-testid=stMain]').getBoundingClientRect(); "
                                                "return frame.left >= main.left - 1 && frame.right <= main.right + 1; }")
        laptop.screenshot(path=str(output / "after-laptop-simulation.png"), full_page=True)
        for tab in ("Mô phỏng", "Tổng quan", "Tuyến và lịch", "Chi tiết", "Đánh giá"):
            laptop.get_by_role("tab", name=tab, exact=True).click()
            assert laptop.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"), tab
            assert laptop.get_by_test_id("stMain").evaluate("el => el.scrollWidth <= el.clientWidth + 1"), tab
        laptop.get_by_role("tab", name="Tuyến và lịch", exact=True).click()
        expect(laptop.locator('img:visible')).to_have_count(2)
        laptop.wait_for_function("[...document.images].every(img => img.complete && img.naturalWidth > 0)")
        laptop.screenshot(path=str(output / "after-laptop-route.png"), full_page=True)
        checks.append("1366x768 laptop: sidebar run, three metrics, all tabs and simulation iframe without overflow")
        page.get_by_role("tab", name="Tổng quan", exact=True).focus()
        page.keyboard.press("ArrowRight")
        expect(page.get_by_role("tab", name="Tuyến và lịch", exact=True)).to_be_focused()
        page.locator(".st-key-run").get_by_role("button").focus()
        page.keyboard.press("Tab")
        assert page.evaluate("document.activeElement.tagName !== 'BODY'")
        checks.append("keyboard arrow navigation across tabs")
        assert not errors, errors
        browser.close()
    report = {"checks": checks, "page_errors": errors, "python": sys.executable}
    (output / "browser-checks.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
