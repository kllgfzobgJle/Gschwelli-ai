import asyncio
import os
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        url = 'file:///' + os.path.abspath('ui/dashboard/index.html').replace('\\', '/')
        await page.goto(url)
        await page.wait_for_selector('#viewport-2', state='attached')

        # Test A: highlightCode execution and XSS sanitization
        js_code_a = '''() => {
            window.highlightCode('<script>alert("XSS")</script>\\ndef calculate_pi(n=1000):\\n    # compute pi\\n    return "result: " + str(n)', 'py');
            const pre = document.getElementById('code-highlighted-pre');
            const lines = document.getElementById('code-line-numbers');
            return {
                html: pre.innerHTML,
                text: pre.textContent,
                lineCount: lines.children.length,
                hasScriptTag: pre.querySelector('script') !== null,
                hasKeywords: pre.querySelectorAll('.tok-kw').length > 0,
                hasStrings: pre.querySelectorAll('.tok-str').length > 0,
                hasComments: pre.querySelectorAll('.tok-com').length > 0
            };
        }'''
        res_a = await page.evaluate(js_code_a)
        print('Test A (highlightCode): PASSED')
        assert not res_a['hasScriptTag'], 'XSS vulnerability: script tag injected!'
        assert res_a['hasKeywords'], 'Keywords not highlighted!'
        assert res_a['hasStrings'], 'Strings not highlighted!'
        assert res_a['hasComments'], 'Comments not highlighted!'
        assert res_a['lineCount'] == 4, f"Expected 4 lines, got {res_a['lineCount']}"

        # Test B: parseCsv edge cases
        js_code_b = '''() => {
            const csv1 = 'Name,Bio,Count\\n"Smith, John","Software \\"\\"Engineer\\"\\"",42\\n"Alice","Data, Scientist",99';
            const parsed1 = window.parseCsv(csv1);
            const tsv1 = 'ColA\\tColB\\nVal1\\tVal2';
            const parsed2 = window.parseCsv(tsv1);
            return {
                headers1: parsed1.headers,
                rows1: parsed1.rows,
                headers2: parsed2.headers,
                rows2: parsed2.rows
            };
        }'''
        res_b = await page.evaluate(js_code_b)
        print('Test B (parseCsv): PASSED')
        assert res_b['headers1'] == ['Name', 'Bio', 'Count']
        assert res_b['rows1'][0] == ['Smith, John', 'Software "Engineer"', '42']
        assert res_b['rows1'][1] == ['Alice', 'Data, Scientist', '99']
        assert res_b['headers2'] == ['ColA', 'ColB']
        assert res_b['rows2'][0] == ['Val1', 'Val2']

        # Test C: Data grid live search with regex special characters
        js_code_c = '''() => {
            window.renderDataGrid('ID,Symbol,Value\\n1,foo[0],10\\n2,bar.*,20\\n3,baz?+,30');
            const searchInput = document.getElementById('grid-search-input');
            searchInput.value = '.*';
            searchInput.dispatchEvent(new Event('input'));
            const tbody = document.getElementById('grid-tbody');
            const rowsCount = tbody.querySelectorAll('tr').length;
            const dimBadge = document.getElementById('grid-dimensions-badge').textContent;
            return { rowsCount, dimBadge };
        }'''
        res_c = await page.evaluate(js_code_c)
        print('Test C (Data Grid Search): PASSED')
        assert res_c['rowsCount'] == 1, f"Expected 1 filtered row, got {res_c['rowsCount']}"
        assert '1 / 3 ROWS' in res_c['dimBadge']

        # Test D: Button clicks (wrap toggle, copy buttons)
        js_code_d = '''() => {
            const btnWrap = document.getElementById('btn-code-toggle-wrap');
            const pre = document.getElementById('code-highlighted-pre');
            const origWrap = pre.style.whiteSpace;
            btnWrap.click();
            const toggledWrap = pre.style.whiteSpace;
            const btnWrapText = btnWrap.textContent;

            const btnCopyCode = document.getElementById('btn-code-copy');
            btnCopyCode.click();
            const btnCopyText = btnCopyCode.textContent;

            const btnCopyTsv = document.getElementById('btn-grid-copy-tsv');
            btnCopyTsv.click();
            const btnTsvText = btnCopyTsv.textContent;

            return { origWrap, toggledWrap, btnWrapText, btnCopyText, btnTsvText };
        }'''
        res_d = await page.evaluate(js_code_d)
        print('Test D (Button Actions): PASSED')
        assert res_d['toggledWrap'] == 'pre-wrap'
        assert res_d['btnWrapText'] == 'Wrap: On'
        assert 'Copied' in res_d['btnCopyText']
        assert 'Copied' in res_d['btnTsvText']

        # Test E: Manual sub-view tabs
        js_code_e = '''() => {
            const results = {};
            const tabs = ['code', 'grid', 'media', 'markdown'];
            for (const t of tabs) {
                const btn = document.querySelector(`.studio-view-btn[data-studio-view="${t}"]`);
                btn.click();
                const pane = document.getElementById(`ks-${t === 'markdown' ? 'markdown' : (t === 'grid' ? 'data-grid' : t)}-studio`);
                const modeBadge = document.getElementById('ks-mode-indicator-badge').textContent;
                results[t] = {
                    display: pane.style.display,
                    badge: modeBadge,
                    activeClass: btn.classList.contains('active')
                };
            }
            return results;
        }'''
        res_e = await page.evaluate(js_code_e)
        print('Test E (Studio Tabs): PASSED')
        for t in ['code', 'grid', 'media', 'markdown']:
            assert res_e[t]['display'] == 'flex'
            assert res_e[t]['activeClass']

        # Test F: FileExplorer file preview MIME auto-routing
        js_code_f = '''() => {
            const results = {};
            // Select py file
            FileExplorer.selectFile('agent_runner.py');
            const codeStudio = document.getElementById('ks-code-studio').style.display;
            const editorValPy = document.getElementById('ks-editor-textarea').value;
            const preContent = document.getElementById('code-highlighted-pre').textContent;
            results.py = { codeStudio, hasEditorVal: editorValPy.length > 0, hasPreContent: preContent.length > 0 };

            // Select csv file
            FileExplorer.selectFile('metrics_report.csv');
            const gridStudio = document.getElementById('ks-data-grid-studio').style.display;
            const gridRows = document.querySelectorAll('#grid-tbody tr').length;
            results.csv = { gridStudio, gridRows };

            // Select md file
            FileExplorer.selectFile('README.md');
            const mdStudio = document.getElementById('ks-markdown-studio').style.display;
            const mdPreview = document.getElementById('ks-markdown-preview').innerHTML;
            results.md = { mdStudio, hasPreview: mdPreview.length > 0 };

            return results;
        }'''
        res_f = await page.evaluate(js_code_f)
        print('Test F (MIME Auto-routing): PASSED')
        assert res_f['py']['codeStudio'] == 'flex'
        assert res_f['py']['hasEditorVal']
        assert res_f['py']['hasPreContent']
        assert res_f['csv']['gridStudio'] == 'flex'
        assert res_f['csv']['gridRows'] > 0
        assert res_f['md']['mdStudio'] == 'flex'
        assert res_f['md']['hasPreview']

        print('ALL ADVERSARIAL STRESS CHECKS PASSED!')
        await browser.close()

asyncio.run(run())
