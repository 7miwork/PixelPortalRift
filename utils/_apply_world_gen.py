
from pathlib import Path
import sys

content = Path('utils/_world_gen_new.txt').read_text()
Path('utils/world_gen.py').write_text(content)
print('world_gen.py written:', len(content.splitlines()), 'lines')
