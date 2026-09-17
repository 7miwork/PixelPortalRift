
from pathlib import Path
import sys

OUT = Path(__file__).with_name('world_gen.py')

content = Path('_world_gen_template.txt').read_text(encoding='utf-8')
OUT.write_text(content, encoding='utf-8')
print(f'Wrote {OUT} ({len(content.splitlines())} lines)')
