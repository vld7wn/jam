"""Download the matching upstream addon and prepare an installable ZIP.
Does not change Blender preferences, scenes, or existing addons.
"""
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

COMMIT = '7a1538c432e8382732ade4db65cadb8999918805'
url = f'https://github.com/carlosh7/blender-mcp/archive/{COMMIT}.zip'
out = Path(__file__).resolve().parent / 'blender_mcp_ultra.zip'
prefix = f'blender-mcp-{COMMIT}/addon/'
count = 0
with urlopen(url, timeout=90) as response:
    data = response.read()
with ZipFile(BytesIO(data)) as source, ZipFile(out, 'w') as target:
    for item in source.infolist():
        if not item.filename.startswith(prefix) or item.is_dir():
            continue
        relative = item.filename[len(prefix):]
        if '..' in Path(relative).parts:
            raise ValueError('Unsafe archive path')
        target.writestr('blender_mcp_ultra/' + relative, source.read(item))
        count += 1
with ZipFile(out) as result:
    assert 'blender_mcp_ultra/__init__.py' in result.namelist()
    assert result.testzip() is None
print(f'Prepared {out} ({count} files), upstream commit {COMMIT}')
