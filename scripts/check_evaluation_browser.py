"""Exercise portable upload, filters and downloads in the real Streamlit browser.

Requires Playwright and installed Microsoft Edge, like the existing demo checks.
"""
import argparse
import csv
import io
import json
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from playwright.sync_api import expect, sync_playwright
from src.evaluation import evaluation_tables, load_evaluation
from src.evaluation_figures import GROUP_LABELS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8517")
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "results/evaluation_browser_audit")
    args = parser.parse_args()
    payload = load_evaluation(args.evaluation)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    errors, checks = [], []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(args.url)
        expect(page.locator(".st-key-run").get_by_role("button")).to_be_visible(timeout=45000)
        page.get_by_text("Đánh giá benchmark", exact=True).click()
        expect(page.get_by_role("heading", name="Đánh giá benchmark", exact=True)).to_be_visible()
        page.get_by_test_id("stFileUploader").locator('input[type="file"]').set_input_files(str(args.evaluation.resolve()))

        def settled():
            expect(page.get_by_test_id("stStatusWidget")).to_have_count(0, timeout=60000)
            expect(page.get_by_test_id("stSkeleton")).to_have_count(0, timeout=60000)
            expect(page.locator('[data-stale="true"]')).to_have_count(0, timeout=60000)
            expect(page.get_by_test_id("stException")).to_have_count(0)

        def open_tab(name):
            tab = page.get_by_role("tab", name=name, exact=True)
            tab.click()
            expect(tab).to_have_attribute("aria-selected", "true", timeout=60000)
            settled()

        expect(page.get_by_role("tab", name="Tổng hợp", exact=True)).to_be_visible(timeout=60000)
        settled()
        checks.append("portable upload before any simulation")
        page.screenshot(path=str(output / "benchmark-summary-desktop.png"), full_page=True, animations="disabled")

        def select(key, value):
            widget = page.locator(f".st-key-{key}")
            control = widget.get_by_role("combobox")
            control.press("Escape")
            widget.get_by_role("button", name="Open", exact=True).click()
            option = page.get_by_role("option", name=value, exact=True)
            expect(option).to_be_visible(timeout=15000)
            option.click()
            expect(control).to_have_value(value)
            settled()

        group = next((g for g in payload["groups"] if g["name"] == "scalability"), payload["groups"][0])
        group_label = GROUP_LABELS.get(group["name"], group["name"])
        open_tab("Biểu đồ")
        image = page.locator('img:visible').first
        expect(image).to_be_visible(timeout=60000)
        page.wait_for_function("[...document.images].every(i => i.complete && i.naturalWidth > 0)")
        previous_image = image.get_attribute("src")
        previous_group = page.locator(".st-key-evaluation_group").get_by_role("combobox").input_value()
        select("evaluation_group", group_label)
        open_tab("Biểu đồ")
        # The group input updates before the server finishes the cohort's charts.
        quality_label = re.compile(rf"^Chất lượng phương án · {re.escape(group_label)}(?: · [Tt]rang \d+)?$")
        figure_choice = page.locator(".st-key-evaluation_figure").get_by_role("combobox")
        expect(figure_choice).to_have_value(quality_label, timeout=60000)
        if previous_group != group_label:
            expect(image).not_to_have_attribute("src", previous_image, timeout=60000)
        page.wait_for_function("[...document.images].every(i => i.complete && i.naturalWidth > 0)")
        settled()
        reference = "B2" if "B2" in group["config"]["methods"] else "B0"
        if page.locator(".st-key-evaluation_reference").get_by_role("combobox").input_value() != reference:
            select("evaluation_reference", reference)
        open_tab("Tổng hợp")
        with page.expect_download() as event:
            page.get_by_role("button", name="Tải bảng tổng hợp (CSV)", exact=True).click()
        destination = output / "downloaded-summary.csv"
        event.value.save_as(destination)
        actual = list(csv.DictReader(io.StringIO(destination.read_text(encoding="utf-8-sig"))))
        expected = evaluation_tables({**payload, "groups": [group]}, reference)["summary"]
        assert len(actual) == len(expected)
        for row, wanted in zip(actual, expected):
            assert row["group"] == wanted["group"] and row["method"] == wanted["method"]
            assert abs(float(row["mean_improvement_pct"]) - wanted["mean_improvement_pct"]) < 1e-8
        checks.append("group/reference filtering and downloaded CSV matches shared statistics")
        open_tab("Biểu đồ")
        expect(page.locator('img:visible').first).to_be_visible(timeout=60000)
        page.wait_for_function("[...document.images].every(i => i.complete && i.naturalWidth > 0)")
        page.screenshot(path=str(output / "benchmark-charts-desktop.png"), full_page=True, animations="disabled")
        expect(page.get_by_role("button", name="Tải hình PDF", exact=True)).to_have_count(0)
        expect(page.get_by_role("button", name="Tải hình PNG", exact=True)).to_have_count(1)
        with page.expect_download() as event:
            page.get_by_role("button", name="Tải hình PNG", exact=True).click()
        destination = output / "downloaded-chart.png"
        event.value.save_as(destination)
        assert destination.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        checks.append("single chart display and PNG-only download")
        report_image = page.locator('img:visible').first.get_attribute("src")
        select("evaluation_style", "Slide")
        expect(page.locator(".st-key-evaluation_figure")).to_be_visible(timeout=60000)
        expect(page.locator('img:visible').first).not_to_have_attribute("src", report_image, timeout=60000)
        settled()
        with page.expect_download() as event:
            page.get_by_role("button", name="Tải hình PNG", exact=True).last.click()
        destination = output / "downloaded-presentation.png"
        event.value.save_as(destination)
        png = destination.read_bytes()
        assert png.startswith(b"\x89PNG\r\n\x1a\n")
        width, height = struct.unpack(">II", png[16:24])
        assert width * 9 == height * 16, (width, height)
        page.screenshot(path=str(output / "benchmark-presentation-desktop.png"), full_page=True, animations="disabled")
        checks.append("presentation figure selection and exact 16:9 PNG download")
        page.set_viewport_size({"width": 1366, "height": 768})
        open_tab("Tổng hợp")
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
        assert page.get_by_test_id("stMain").evaluate("el => el.scrollWidth <= el.clientWidth + 1")
        page.screenshot(path=str(output / "benchmark-summary-laptop.png"), full_page=True, animations="disabled")
        open_tab("Biểu đồ")
        expect(figure_choice).to_be_visible()
        expect(image).to_be_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
        assert page.get_by_test_id("stMain").evaluate("el => el.scrollWidth <= el.clientWidth + 1")
        page.screenshot(path=str(output / "benchmark-chart-laptop.png"), full_page=True, animations="disabled")
        checks.append("1366x768 laptop summary and chart without main/page horizontal overflow")
        invalid = output / "invalid-evaluation.json"
        invalid.write_text('{"schema_version":999}', encoding="utf-8")
        page.get_by_test_id("stFileUploader").locator('input[type="file"]').set_input_files(str(invalid))
        expect(page.get_by_text("Tệp đánh giá không hợp lệ.", exact=False)).to_be_visible(timeout=45000)
        settled()
        expect(page.get_by_test_id("stDataFrame")).to_have_count(0)
        checks.append("invalid replacement rejected without stale tables")
        browser.close()
    assert not errors, errors
    (output / "checks.json").write_text(json.dumps({"checks": checks, "page_errors": errors}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Passed {len(checks)} browser acceptance checks: {output}")


if __name__ == "__main__":
    main()
