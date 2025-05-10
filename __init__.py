bl_info = {
    "name": "BlenDR",
    "author": "spicybung",
    "version": (0, 0, 1),   # Not out yet!
    "blender": (2, 93, 0),  # Testing on Blender 3.8 & Blender 4.4
    "location": "File > Import",
    "description": "Tools for editing RAGE Engine & openFormat file formats",
    "category": "Import-Export"
}

from .OFLib import import_iv_mesh_odr
from .REops import wdd_importer, wdr_importer
from .RELib import wdr

def register():
    import_iv_mesh_odr.register()
    wdd_importer.register()
    wdr_importer.register()
    wdr.register() 

def unregister():
    import_iv_mesh_odr.unregister()
    wdd_importer.unregister()
    wdr_importer.unregister()
    wdr.unregister()
