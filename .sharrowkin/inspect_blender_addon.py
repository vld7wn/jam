from pathlib import Path
import zipfile

archive = Path('blender_mcp/mcp-1.0.3.zip')
with zipfile.ZipFile(archive) as z:
    print('Archive entries:', z.namelist()[:60])
    for name in z.namelist():
        if name.endswith(('.py', '.toml')):
            text = z.read(name).decode('utf-8', errors='replace')
            print('SOURCE', name, 'bytes', len(text), text[:4500] if name in ('blender_manifest.toml', '__init__.py', 'mcp_to_blender_server.py') else '')
            lines = text.splitlines()
            matches = [i for i, line in enumerate(lines) if any(term in line.lower() for term in ('bl_info', 'protocol_version', 'get_addon_status', 'get_capabilities', '"version"', '"name"'))]
            if matches:
                print('\nFILE:', name)
                shown = set()
                for i in matches:
                    for j in range(max(0, i-1), min(len(lines), i+5)):
                        if j not in shown:
                            print(f'{j+1}: {lines[j]}')
                            shown.add(j)
