import asyncio
import os
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

async def stress_test_studio():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        target_path = os.path.abspath('ui/dashboard/index.html').replace('\\', '/')
        await page.goto(f'file:///{target_path}')
        await page.wait_for_load_state('networkidle')
        
        errors = []
        page.on('pageerror', lambda err: errors.append(str(err)))

        print('--- Stress Test 1: Empty and Edge Inputs for parseCsv ---')
        # Empty string
        res_empty = await page.evaluate('(s) => window.parseCsv(s)', '')
        assert res_empty == {'headers': [], 'rows': []}

        # Null / undefined
        res_null = await page.evaluate('(s) => window.parseCsv(s)', None)
        assert res_null == {'headers': [], 'rows': []}

        # Only whitespace
        res_ws = await page.evaluate('(s) => window.parseCsv(s)', '   \n\n  \t  ')
        assert res_ws == {'headers': [], 'rows': []}

        # Single row with no newline
        res_single = await page.evaluate('(s) => window.parseCsv(s)', 'a,b,c')
        assert res_single['headers'] == ['a', 'b', 'c']
        assert res_single['rows'] == []

        # Complex quotes and commas
        complex_csv = 'col1,col2\n"val1, with comma","val2 ""with escaped"" quotes"'
        res_complex = await page.evaluate('(s) => window.parseCsv(s)', complex_csv)
        assert res_complex['headers'] == ['col1', 'col2']
        assert res_complex['rows'] == [['val1, with comma', 'val2 "with escaped" quotes']]
        print('parseCsv stress passed!')

        print('--- Stress Test 2: Edge Inputs for highlightCode ---')
        # Empty string
        await page.evaluate('(c) => window.highlightCode(c, "py")', '')
        lines_count_empty = await page.locator('#code-line-numbers .code-line-number').count()
        assert lines_count_empty == 1

        # Null / undefined
        await page.evaluate('(c) => window.highlightCode(c, "js")', None)
        lines_count_null = await page.locator('#code-line-numbers .code-line-number').count()
        assert lines_count_null == 1

        # Code with HTML tags (XSS check)
        xss_code = '<script>alert("xss")</script>\n<b>bold</b>'
        await page.evaluate('(c) => window.highlightCode(c, "html")', xss_code)
        # Ensure raw <script> is not present in DOM as executable element
        script_elements = await page.locator('#code-highlighted-pre script').count()
        assert script_elements == 0, 'XSS vulnerability: <script> was parsed into DOM!'
        print('highlightCode stress passed!')

        print('--- Stress Test 3: Large CSV in Data Grid ---')
        await page.evaluate('() => window.switchViewport("2")')
        await page.click('#btn-view-grid')

        large_csv = 'id,name,value\n' + '\n'.join([f'{i},row_{i},{i*10}' for i in range(500)])
        await page.evaluate('(c) => window.renderDataGrid(c)', large_csv)
        tr_count = await page.locator('#grid-tbody tr').count()
        assert tr_count == 500
        
        # Filter on large grid
        await page.fill('#grid-search-input', 'row_499')
        filtered_count = await page.locator('#grid-tbody tr').count()
        assert filtered_count == 1
        print('Large CSV stress passed!')

        assert len(errors) == 0, f'Page errors encountered: {errors}'
        print('ALL STRESS TESTS PASSED CLEANLY!')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(stress_test_studio())
