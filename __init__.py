# BlenDR - Blender scripts to work with RAGE/openFormat file types 
# 2024 - 2025 SpicyBung

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

bl_info = {
    "name": "BlenDR",
    "author": "spicybung",
    "version": (0, 0, 1),
    "blender": (2, 93, 0),
    "location": "File > Import",
    "description": "Import/Export RAGE/openFormat file types",
    "category": "Import-Export",
    "warning": "Work in progress - not all formats fully supported yet"
}

from .interface import import_mesh_odr
from .REops import wdr

def register():
    import_mesh_odr.register()
    wdr.register()

def unregister():
    import_mesh_odr.unregister()
    wdr.unregister()
