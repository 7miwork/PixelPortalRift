
from pathlib import Path

new_content = open('utils/world_gen_new_content.txt', 'r').read()
path = Path('utils/world_gen.py')
path.write_text(new_content.lstrip())
print(f'world_gen.py überschrieben. Zeilen: {len(new_content.splitlines())}')
