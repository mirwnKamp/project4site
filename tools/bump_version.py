"""Cache-busting: stamp every local scripts/*.css|js link in the pages with ?v=<now>.

Run before each push that changes anything in scripts/, so browsers (iPhone Safari above all)
fetch the new files instead of their cached copy: python tools/bump_version.py
"""
import glob
import os
import re
import time

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
stamp = time.strftime('%Y%m%d%H%M')
link = re.compile(r'((?:src|href)="(?:\.\./)?scripts/[\w.-]+\.(?:css|js))(?:\?v=\w+)?"')
for f in glob.glob(os.path.join(SITE, '*.html')) + glob.glob(os.path.join(SITE, 'account', '*.html')):
    text = open(f, encoding='utf-8').read()
    new, n = link.subn(lambda m: f'{m.group(1)}?v={stamp}"', text)
    if new != text:
        open(f, 'w', encoding='utf-8', newline='').write(new)
        print(os.path.relpath(f, SITE), n)
print('version', stamp)
