import asyncio
import os
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

async def verify_viewport2():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Load local dashboard file
        target_path = os.path.abspath('ui/dashboard/index.html').replace('\\', '/')
        url = f'file:///{target_path}'
        print(f'Navigating to {url}...')
        await page.goto(url)
        await page.wait_for_load_state('networkidle')
        
        errors = []
        page.on('pageerror', lambda err: errors.append(str(err)))

        print('=== 0. Switch to Viewport 2 ===')
        await page.evaluate('() => window.switchViewport("2")')
        vp2_active = await page.evaluate('() => document.getElementById("viewport-2").classList.contains("active")')
        print(f'Viewport 2 active: {vp2_active}')
        assert vp2_active

        print('=== 1. Check window bindings ===')
        has_highlight = await page.evaluate('typeof window.highlightCode === "function"')
        has_parse_csv = await page.evaluate('typeof window.parseCsv === "function"')
        has_render_studio = await page.evaluate('typeof window.renderArtifactStudio === "function"')
        print(f'highlightCode: {has_highlight}, parseCsv: {has_parse_csv}, renderArtifactStudio: {has_render_studio}')
        assert has_highlight and has_parse_csv and has_render_studio

        print('=== 2. Check highlightCode tokenization ===')
        # Activate code view
        await page.click('#btn-view-code')
        code_sample = (
            'def calculate_metrics(data, threshold=0.95):\n'
            '    # Process batch\n'
            '    result = "done"\n'
            '    return result'
        )
        await page.evaluate('(code) => window.highlightCode(code, "py")', code_sample)
        
        kw_count = await page.locator('#code-highlighted-pre .tok-kw').count()
        fn_count = await page.locator('#code-highlighted-pre .tok-fn').count()
        com_count = await page.locator('#code-highlighted-pre .tok-com').count()
        str_count = await page.locator('#code-highlighted-pre .tok-str').count()
        num_count = await page.locator('#code-highlighted-pre .tok-num').count()
        lines_count = await page.locator('#code-line-numbers .code-line-number').count()
        print(f'Tokens -> kw: {kw_count}, fn: {fn_count}, com: {com_count}, str: {str_count}, num: {num_count}, lines: {lines_count}')
        assert kw_count >= 2, f'Expected kw >= 2, got {kw_count}'  # def, return
        assert fn_count >= 1, f'Expected fn >= 1, got {fn_count}'  # calculate_metrics
        assert com_count >= 1, f'Expected com >= 1, got {com_count}' # # Process batch
        assert str_count >= 1, f'Expected str >= 1, got {str_count}' # "done"
        assert num_count >= 1, f'Expected num >= 1, got {num_count}' # 0.95
        assert lines_count == 4, f'Expected lines == 4, got {lines_count}'

        print('=== 3. Check Code Interactive Buttons Wiring ===')
        # Code wrap toggle
        pre_wrap_before = await page.evaluate('() => document.getElementById("code-highlighted-pre").style.whiteSpace')
        await page.click('#btn-code-toggle-wrap')
        pre_wrap_after = await page.evaluate('() => document.getElementById("code-highlighted-pre").style.whiteSpace')
        wrap_btn_text = await page.locator('#btn-code-toggle-wrap').inner_text()
        print(f'Wrap before: {pre_wrap_before}, after: {pre_wrap_after}, btn: {wrap_btn_text}')
        assert pre_wrap_after == 'pre-wrap'
        assert 'Wrap: On' in wrap_btn_text

        # Code copy button
        await page.click('#btn-code-copy')
        copy_text = await page.locator('#btn-code-copy').inner_text()
        print('Copy code btn text:', copy_text)
        assert 'Copied' in copy_text

        print('=== 4. Check parseCsv quote handling ===')
        csv_sample = (
            'id,name,notes,score\n'
            '1,Alpha,"Standard, unquoted",42\n'
            '2,Beta,"Quotes with ""escaped"" marks",99\n'
            '3,Gamma,Plain string,88'
        )
        res = await page.evaluate('(csv) => window.parseCsv(csv)', csv_sample)
        print('parseCsv headers:', res['headers'])
        print('parseCsv rows count:', len(res['rows']))
        print('parseCsv row 0:', res['rows'][0])
        print('parseCsv row 1:', res['rows'][1])
        assert res['headers'] == ['id', 'name', 'notes', 'score']
        assert len(res['rows']) == 3
        assert res['rows'][0][2] == 'Standard, unquoted'
        assert res['rows'][1][2] == 'Quotes with "escaped" marks'

        print('=== 5. Check Data Grid Rendering & Searching ===')
        # Activate Grid view
        await page.click('#btn-view-grid')
        await page.evaluate('(csv) => window.renderDataGrid(csv)', csv_sample)
        th_count = await page.locator('#grid-thead th').count()
        tr_count = await page.locator('#grid-tbody tr').count()
        dim_text = await page.locator('#grid-dimensions-badge').inner_text()
        print(f'Grid -> th_count: {th_count}, tr_count: {tr_count}, dim_text: {dim_text}')
        assert th_count == 5, f'Expected 5 headers, got {th_count}'  # # row-num + 4 cols
        assert tr_count == 3, f'Expected 3 rows, got {tr_count}'
        assert '3 ROWS' in dim_text

        # Test filter search
        await page.fill('#grid-search-input', 'Beta')
        filtered_tr_count = await page.locator('#grid-tbody tr').count()
        filtered_dim = await page.locator('#grid-dimensions-badge').inner_text()
        print(f'Search "Beta" -> tr_count: {filtered_tr_count}, dim_text: {filtered_dim}')
        assert filtered_tr_count == 1
        assert '1 / 3 ROWS' in filtered_dim

        await page.fill('#grid-search-input', '')
        reset_tr_count = await page.locator('#grid-tbody tr').count()
        assert reset_tr_count == 3

        # Grid copy button
        await page.click('#btn-grid-copy-tsv')
        grid_copy_text = await page.locator('#btn-grid-copy-tsv').inner_text()
        print('Copy grid btn text:', grid_copy_text)
        assert 'Copied' in grid_copy_text

        print('=== 6. Check Studio Sub-View Switching ===')
        # Click Code view tab
        await page.click('#btn-view-code')
        code_vis = await page.evaluate('() => document.getElementById("ks-code-studio").style.display')
        md_vis = await page.evaluate('() => document.getElementById("ks-markdown-studio").style.display')
        mode_badge = await page.locator('#ks-mode-indicator-badge').inner_text()
        print(f'Code tab clicked -> code_display: {code_vis}, md_display: {md_vis}, badge: {mode_badge}')
        assert code_vis == 'flex'
        assert md_vis == 'none'
        assert mode_badge == 'CODE'

        # Click Markdown view tab
        await page.click('#btn-view-markdown')
        md_vis2 = await page.evaluate('() => document.getElementById("ks-markdown-studio").style.display')
        mode_badge3 = await page.locator('#ks-mode-indicator-badge').inner_text()
        print(f'Markdown tab clicked -> md_display: {md_vis2}, badge: {mode_badge3}')
        assert md_vis2 == 'flex'
        assert mode_badge3 == 'MARKDOWN'

        print('=== 7. Check FileExplorer previewInViewport2 MIME routing ===')
        # Click agent_runner.py in tree
        py_item = page.locator('.file-tree-item', has_text='agent_runner.py').first
        if await py_item.count() > 0:
            await py_item.click()
            code_vis_tree = await page.evaluate('() => document.getElementById("ks-code-studio").style.display')
            ks_editor_val = await page.evaluate('() => document.getElementById("ks-editor-textarea").value')
            badge_tree = await page.locator('#ks-mode-indicator-badge').inner_text()
            print(f'Clicked agent_runner.py -> code_studio: {code_vis_tree}, badge: {badge_tree}')
            assert code_vis_tree == 'flex'
            assert badge_tree == 'PY'
            assert len(ks_editor_val) > 0

        # Click metrics_report.csv in tree
        csv_item = page.locator('.file-tree-item', has_text='metrics_report.csv').first
        if await csv_item.count() > 0:
            await csv_item.click()
            grid_vis_tree = await page.evaluate('() => document.getElementById("ks-data-grid-studio").style.display')
            badge_csv = await page.locator('#ks-mode-indicator-badge').inner_text()
            print(f'Clicked metrics_report.csv -> grid_studio: {grid_vis_tree}, badge: {badge_csv}')
            assert grid_vis_tree == 'flex'
            assert badge_csv == 'DATA GRID'

        assert len(errors) == 0, f'Page errors: {errors}'
        print('ALL VIEWPORT 2 CHECKS PASSED WITH ZERO ERRORS!')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(verify_viewport2())
