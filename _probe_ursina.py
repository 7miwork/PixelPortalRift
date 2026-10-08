import sys, os
print('ARGS:', sys.argv)
print('CWD:', os.getcwd())
import ursina.application as a
print('asset_folder:', a.asset_folder)
print('parent:', a.asset_folder.parent)
