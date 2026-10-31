import ast
from pathlib import Path
p = Path('blender_mcp/jam2d_pipeline.py')
ast.parse(p.read_text(encoding='utf-8'), filename=str(p))
print('Blender exporter Python syntax: PASS')
