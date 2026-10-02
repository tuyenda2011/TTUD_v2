"""Capture replay layout and canvas labels at desktop and narrow viewports."""
import argparse
import json
import math
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright

from demo.simulation import render_simulation
from src.generator import generate_scenario
from src.models import read_instance
from src.solver import solve
from src.units import KRIS_DISPLAY_CONVENTION, display_snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check', action='store_true', help='Fail on hidden or distorted content')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    cases = [('synthetic-3', generate_scenario('double_block', n=30, pickers=3)),
             ('synthetic-12', generate_scenario('double_block', n=30, pickers=12)),
             ('kris', read_instance(ROOT / 'data/processed/kris_small/instances_6_1.json'))]
    records = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        for name, instance in cases:
            raw = {'instance': instance.to_dict(), 'results': {'B0': solve(instance, 'B0')}}
            view = display_snapshot(raw, KRIS_DISPLAY_CONVENTION)
            instance = type(instance).from_dict(view['instance'])
            with patch('demo.simulation.components.html') as component:
                render_simulation(instance, view['results']['B0'])
            html = output / f'{name}.html'
            html.write_text(component.call_args.args[0], encoding='utf-8')
            for width, height in [(1440, 750), (768, 750), (390, 750), (320, 568), (280, 568)]:
                page = browser.new_page(viewport={'width': width, 'height': height})
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.add_init_script("""(() => {
                  window.pickerLabels = {};
                  window.badges = [];
                  const original = CanvasRenderingContext2D.prototype.fillText;
                  CanvasRenderingContext2D.prototype.fillText = function(text, x, y, ...args) {
                    if (/^P\\d+$/.test(text)) window.pickerLabels[text] = {x, y};
                    if (String(text).startsWith('+') || String(text).startsWith('Soạn')) {
                      const width = this.measureText(text).width;
                      window.badges.push({text, left:x-width/2, right:x+width/2, y});
                    }
                    return original.call(this, text, x, y, ...args);
                  };
                })();""")
                page.goto(html.as_uri())
                page.locator('#resetBtn').click()
                page.wait_for_function('Object.keys(window.pickerLabels).length === simData.pickers.length')
                page.screenshot(path=str(output / f'{name}-{width}.png'))
                record = page.evaluate("""() => {
                  const stage = document.querySelector('#stageWrap');
                  const r = stage.getBoundingClientRect();
                  const labels = window.pickerLabels;
                  const overflows = [...document.querySelectorAll('.picker-card, .picker-card-header, [id^=card-load]')]
                    .filter(el => el.scrollWidth > el.clientWidth + 1)
                    .map(el => ({id: el.id, text: el.textContent, width: el.clientWidth, scroll: el.scrollWidth}));
                  return {labels, stage: {width:r.width, height:r.height},
                    canvas: {width:simCanvas.clientWidth, height:simCanvas.clientHeight,
                             pixelWidth:simCanvas.width, pixelHeight:simCanvas.height},
                    transform: {width:getTransform().w, height:getTransform().h},
                    overflows, bodyOverflow: document.body.scrollWidth > innerWidth,
                    uniquePositions: new Set(Object.values(labels).map(p => `${p.x},${p.y}`)).size};
                }""")
                movement = page.evaluate("""async () => {
                  const segments = simData.pickers.flatMap(p => p.segments);
                  const travel = segments.find(s => s.state === 'traveling' && s.t_end > s.t_start);
                  if (travel) {
                    simTime = (travel.t_start + travel.t_end) / 2;
                    await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
                  }
                  const points = Object.values(pickerTrails).flat();
                  const inModelSpace = points.every(p => p.x >= simData.bounds.min_x && p.x <= simData.bounds.max_x
                    && p.y >= simData.bounds.min_y && p.y <= simData.bounds.max_y);
                  resetBtn.click();
                  const resetCleared = Object.values(pickerTrails).every(trail => trail.length === 0);
                  const pick = segments.filter(s => s.state === 'picking' && s.t_end > s.t_start)
                    .sort((a, b) => b.x1 - a.x1)[0];
                  if (pick) {
                    timelineSlider.value = (pick.t_start + pick.t_end) / 2;
                    timelineSlider.dispatchEvent(new Event('input', {bubbles:true}));
                    window.badges = [];
                    await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
                  }
                  const badges = window.badges.slice();
                  const badgesInside = badges.every(b => b.left >= 0 && b.right <= getTransform().w
                    && b.y >= 0 && b.y <= getTransform().h);
                  return {trailPointCount:points.length, trailsInModelSpace:inModelSpace,
                          resetCleared, badges, badgesInside};
                }""")
                page.screenshot(path=str(output / f'{name}-{width}-picking.png'))
                page.locator('#viewSelect').select_option(str(instance.operations.pickers))
                focused_visible = page.evaluate("""() => {
                  const card = document.querySelector(`#card-p${simData.pickers.length}`).getBoundingClientRect();
                  const hud = hudGrid.getBoundingClientRect();
                  return card.top >= hud.top - 1 && card.bottom <= hud.bottom + 1;
                }""")
                record.update(movement=movement, focused_card_visible=focused_visible)
                page.locator('#viewSelect').select_option('all')
                page.evaluate("""async () => {
                  const setup = simData.pickers.flatMap(p => p.segments)
                    .find(s => s.state === 'setup' && s.t_end > s.t_start);
                  if (setup) {
                    timelineSlider.value = (setup.t_start + setup.t_end) / 2;
                    timelineSlider.dispatchEvent(new Event('input', {bubbles:true}));
                    await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
                  }
                }""")
                page.screenshot(path=str(output / f'{name}-{width}-setup.png'))
                record.update(case=name, viewport={'width': width, 'height': height}, page_errors=errors)
                records.append(record)
                page.close()
        browser.close()
    (output / 'checks.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
    if args.check:
        for record in records:
            labels = list(record['labels'].values())
            assert record['uniquePositions'] == len(labels), record
            assert all(math.hypot(a['x'] - b['x'], a['y'] - b['y']) >= 18 - 1e-7
                       for i, a in enumerate(labels) for b in labels[i + 1:]), record
            canvas = record['canvas']
            assert abs(canvas['pixelWidth'] / canvas['width'] - canvas['pixelHeight'] / canvas['height']) < .01, record
            assert not record['bodyOverflow'] and not record['overflows'], record
            assert record['focused_card_visible'] and not record['page_errors'], record
            movement = record['movement']
            assert movement['trailsInModelSpace'] and movement['resetCleared'] and movement['badgesInside'], record
    print(f"Captured {len(records)} visual cases; checks={'PASS' if args.check else 'inspection only'}")


if __name__ == '__main__':
    main()
