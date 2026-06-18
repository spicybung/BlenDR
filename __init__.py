# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#      *     *       *                 *       *       *         *    #
#  *      //   ) )      *        *       //    ) ) //   ) )           #
#        //___/ /  //  ___   *    __ *  //    / / //___/ /     *      #
#   *   / __  (   // //___) ) //   ) ) //    / / / ___ (              #
#      //    ) ) // //       //   / / //    / / //   | |   *      *   #
#     //____/ / // ((____   //   / / //____/ / //    | |              #
# BlenDR - Blender scripts to work with R* RAGE/openFormat file types #
# 2024 - 2025 SpicyBung                                               #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
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
    "version": (0, 0, 1),   # Not out yet!
    "blender": (2, 93, 0),  # Testing on Blender 3.8, Blender 4.4, & newer betas
    "location": "File > Import/Export > BlenDR",
    "description": "Tools for editing RAGE Engine & openFormat file formats",
    "category": "Import-Export"
}

import bpy

from bpy.types import Menu

from .REops import wdd_importer, wdr_importer
from .oFOps import import_iv_mesh_odr, export_iv_mesh_odr


class BLENDR_MT_import(Menu):
    bl_idname = "BLENDR_MT_import"
    bl_label = "BlenDR"

    def draw(self, context):
        layout = self.layout
        layout.operator(wdr_importer.IMPORT_OT_wdr_reader.bl_idname, text="RAGE IV Drawable (.wdr)")
        layout.operator(wdd_importer.IMPORT_OT_wdd_importer.bl_idname, text="RAGE IV Drawable Dictionary (.wdd)")
        layout.separator()
        layout.operator(import_iv_mesh_odr.ImportOpenIVFormats.bl_idname, text="OpenIV openFormats (.odr/.mesh)")


class BLENDR_MT_export(Menu):
    bl_idname = "BLENDR_MT_export"
    bl_label = "BlenDR"

    def draw(self, context):
        self.layout.operator(export_iv_mesh_odr.ExportODR.bl_idname, text="OpenIV openFormat Drawable (.odr)")


classes = (
    BLENDR_MT_import,
    BLENDR_MT_export,
)


def draw_import_menu(self, context):
    self.layout.menu(BLENDR_MT_import.bl_idname, text="BlenDR")


def draw_export_menu(self, context):
    self.layout.menu(BLENDR_MT_export.bl_idname, text="BlenDR")


def register():
    wdr_importer.register()
    wdd_importer.register()
    import_iv_mesh_odr.register()
    export_iv_mesh_odr.register()

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(draw_import_menu)
    bpy.types.TOPBAR_MT_file_export.append(draw_export_menu)


def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(draw_export_menu)
    bpy.types.TOPBAR_MT_file_import.remove(draw_import_menu)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    export_iv_mesh_odr.unregister()
    import_iv_mesh_odr.unregister()
    wdd_importer.unregister()
    wdr_importer.unregister()
