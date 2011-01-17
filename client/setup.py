# setup.py
from distutils.core import setup
import py2exe, psyco

psyco.full()

setup(console=[{"script": "newzBoy.py", "icon_resources": [(1,"ico\\exe.ico")]}],\
      options={"py2exe":{"includes": ["encodings", "encodings.latin_1", "encodings.cp437", "encodings.ascii"]}})
