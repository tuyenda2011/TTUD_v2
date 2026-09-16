"""Browser acceptance test. Requires playwright and installed Microsoft Edge."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from playwright.sync_api import expect, sync_playwright

from warehouse_opt.demo_snapshot import validate_snapshot
from warehouse_opt.models import Instance
from warehouse_opt.validator import validate_solution


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
        expect(page.get_by_role("button", name="Chạy với cấu hình này", exact=True)).to_be_visible()
        expect(page.locator('[data-testid="stSkeleton"]')).to_have_count(0)
        page.screenshot(path=str(output / "after-desktop-empty.png"), full_page=True)

        def select(key, value):
            control = page.locator(f".st-key-{key}").get_by_role("combobox")
            control.scroll_into_view_if_needed()
            control.focus()
            control.press("ArrowDown")
            page.get_by_role("option", name=value, exact=True).click()

        def settled():
            expect(page.get_by_test_id("stStatusWidget")).to_have_count(0, timeout=45000)
            expect(page.get_by_test_id("stSkeleton")).to_have_count(0)

        def run(instance_name):
            page.locator(".st-key-run").get_by_role("button").click()
            expect(page.get_by_text(f"Lần chạy: {instance_name} ·", exact=False)).to_be_visible(timeout=45000)
            settled()
            page.get_by_role("tab", name="Tổng quan", exact=True).click()
            expect(page.get_by_text("Kết quả của phương án", exact=True)).to_be_visible(timeout=45000)
            expect(page.get_by_test_id("stMetric")).to_have_count(3)
            expect(page.get_by_text("Cấu hình bên trái chưa được áp dụng", exact=False)).to_have_count(0)
            settled()

        run("synthetic-n10-seed42")
        page.screenshot(path=str(output / "after-desktop-results.png"), full_page=True)
        page.get_by_role("tab", name="Tuyến & lịch", exact=True).click()
        expect(page.get_by_text("Lịch làm việc", exact=True)).to_be_visible()
        expect(page.locator('img:visible')).to_have_count(2)
        page.wait_for_function("[...document.images].every(img => img.complete && img.naturalWidth > 0)")
        page.screenshot(path=str(output / "after-desktop-route.png"), full_page=True)
        page.locator('img:visible').first.screenshot(path=str(output / "route-10.png"))
        select("route_picker", "Nhân viên 2")
        expect(page.get_by_text("Lịch làm việc", exact=True)).to_be_visible()
        assert page.locator('[data-testid="stException"]').count() == 0
        checks.append("default run and picker/batch filters")

        page.get_by_text("Tải kết quả", exact=True).click()
        with page.expect_download() as download_info:
            page.get_by_role("button", name="Tải toàn bộ lần chạy", exact=True).click()
        snapshot_path = output / "downloaded-snapshot.json"
        download_info.value.save_as(snapshot_path)
        snapshot = validate_snapshot(json.loads(snapshot_path.read_text(encoding="utf-8")))
        with page.expect_download() as download_info:
            page.get_by_role("button", name="Tải nghiệm JSON", exact=True).click()
        result_path = output / "downloaded-solution.json"
        download_info.value.save_as(result_path)
        assert not validate_solution(Instance.from_dict(snapshot["instance"]), json.loads(result_path.read_text(encoding="utf-8")))
        checks.append("download snapshot and solution; independent validation")

        page.locator(".st-key-orders").get_by_role("spinbutton").fill("30")
        page.locator(".st-key-orders").get_by_role("spinbutton").press("Enter")
        expect(page.get_by_text("Đang xem kết quả của cấu hình đã lưu.", exact=False)).to_be_visible()
        run("synthetic-n30-seed42")
        page.get_by_role("tab", name="Tuyến & lịch", exact=True).click()
        expect(page.locator('img:visible')).to_have_count(2)
        page.wait_for_function("[...document.images].every(img => img.complete && img.naturalWidth > 0)")
        page.screenshot(path=str(output / "after-route-30.png"), full_page=True)
        page.locator('img:visible').first.screenshot(path=str(output / "route-30.png"))
        checks.append("changed draft marked stale; 30-order rerun")

        select("source", "JSON tải lên")
        expect(page.locator(".st-key-orders")).to_have_count(0)
        upload = page.locator('.st-key-upload input[type="file"]')
        upload.set_input_files({"name": "invalid.json", "mimeType": "application/json", "buffer": b"{}"})
        expect(page.get_by_role("button", name="Remove invalid.json", exact=True)).to_be_visible()
        settled()
        page.locator(".st-key-run").get_by_role("button").click()
        expect(page.get_by_text("Không thể chạy:", exact=False)).to_be_visible(timeout=30000)
        expect(page.get_by_test_id("stMetric")).to_have_count(0)
        settled()
        page.get_by_role("button", name="Remove invalid.json", exact=True).click()
        expect(page.get_by_role("button", name="Remove invalid.json", exact=True)).to_have_count(0)
        upload.set_input_files(ROOT / "data/synthetic/tiny_4.json")
        expect(page.get_by_role("button", name="Remove tiny_4.json", exact=True)).to_be_visible()
        settled()
        name = json.loads((ROOT / "data/synthetic/tiny_4.json").read_text(encoding="utf-8"))["name"]
        run(name)
        checks.append("JSON invalid clears old result; valid upload runs")

        select("source", "Kris — benchmark tác giả")
        expect(page.locator(".st-key-kris_file")).to_be_visible()
        run("Kris-instances_106_1")
        checks.append("Kris dataset runs")

        mobile = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        mobile.on("pageerror", lambda error: errors.append(str(error)))
        mobile.goto(args.url)
        expect(mobile.get_by_role("button", name="Chạy với cấu hình này", exact=True)).to_be_visible()
        mobile.screenshot(path=str(output / "after-mobile-empty.png"), full_page=True)
        mobile.get_by_role("button", name="Chạy với cấu hình này", exact=True).click()
        expect(mobile.get_by_test_id("stMetric")).to_have_count(3, timeout=45000)
        expect(mobile.get_by_text("Kết quả của phương án", exact=True)).to_be_visible()
        expect(mobile.get_by_test_id("stStatusWidget")).to_have_count(0, timeout=45000)
        mobile.screenshot(path=str(output / "after-mobile-results.png"), full_page=True)
        mobile.get_by_role("tab", name="Tuyến & lịch", exact=True).click()
        expect(mobile.locator('img:visible')).to_have_count(2)
        mobile.wait_for_function("[...document.images].every(img => img.complete && img.naturalWidth > 0)")
        mobile.locator('img:visible').first.scroll_into_view_if_needed()
        mobile.screenshot(path=str(output / "after-mobile-route.png"), full_page=True)
        for tab in ("Tổng quan", "Tuyến & lịch", "Chi tiết"):
            mobile.get_by_role("tab", name=tab, exact=True).click()
            assert mobile.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), tab
            assert mobile.get_by_test_id("stMain").evaluate("el => el.scrollWidth <= el.clientWidth"), tab
        checks.append("390px mobile run, all tabs without page horizontal overflow")
        page.get_by_role("tab", name="Tổng quan", exact=True).focus()
        page.keyboard.press("ArrowRight")
        expect(page.get_by_role("tab", name="Tuyến & lịch", exact=True)).to_be_focused()
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
