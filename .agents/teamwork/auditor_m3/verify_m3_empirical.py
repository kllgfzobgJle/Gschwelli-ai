import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

import time
import socket
import threading
import uvicorn
from playwright.sync_api import sync_playwright
from server.api import create_app

def test_m3():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        port = s.getsockname()[1]

    app = create_app()
    server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=port, log_level='warning'))
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    time.sleep(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 900})
        page.goto(f'http://127.0.0.1:{port}', wait_until='networkidle')
        
        # 1. Verify SOM tags and click
        for mark in ['01', '02', '12', '04']:
            tag = page.locator(f'#som-tag-{mark}')
            assert tag.is_visible(), f'SOM tag {mark} not visible'
        
        page.locator('#som-tag-04').click()
        page.wait_for_timeout(100)
        assert 'active' in page.locator('#som-tag-04').get_attribute('class')
        assert 'active' in page.locator('#leader-line-04').get_attribute('class')
        
        # 2. Verify Camera Zoom & Reset
        mesh_group = page.locator('#cad-mesh-group')
        page.locator('#btn-cam-zoom').click()
        page.wait_for_timeout(100)
        style_zoomed = mesh_group.get_attribute('style')
        assert 'scale(1.15)' in style_zoomed, f'Zoom failed: {style_zoomed}'
        page.locator('#btn-cam-reset').click()
        page.wait_for_timeout(100)
        style_reset = mesh_group.get_attribute('style')
        assert 'scale(1)' in style_reset, f'Reset failed: {style_reset}'
        
        # 3. Verify Re-scan SOM
        frame_before = page.locator('#frame-telemetry').inner_text()
        page.locator('#btn-rescan-som').click()
        page.wait_for_timeout(450)
        frame_after = page.locator('#frame-telemetry').inner_text()
        assert 'FRAME #8185' in frame_after, f'Frame not incremented: {frame_after}'
        
        # 4. Verify Export safety warning using force click
        page.locator('#btn-export-mesh').click(force=True)
        page.wait_for_timeout(100)
        repl_text = page.locator('#repl-logs').inner_text()
        assert 'SEC-810' in repl_text, f'Export safety policy warning not logged to REPL: {repl_text}'
        
        # 5. Verify Menu bar actions
        page.locator('#btn-menu-preview').click()
        page.wait_for_timeout(100)
        repl_text2 = page.locator('#repl-logs').inner_text()
        assert 'Preview compiled' in repl_text2, 'Preview action not logged'
        
        # 6. Verify Shutter flash on capture
        page.locator('#btn-capture-frame').click()
        page.wait_for_timeout(100)
        repl_text3 = page.locator('#repl-logs').inner_text()
        assert 'Frame #8185 captured' in repl_text3, f'Capture not logged: {repl_text3}'

        browser.close()

    print('ALL EMPIRICAL M3 INTERACTION CHECKS PASSED!')

if __name__ == '__main__':
    test_m3()
    sys.exit(0)
