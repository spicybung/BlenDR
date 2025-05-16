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

import io
import os
import bpy
import zlib

from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty

from ..RELib.wdd import (
    read_wdd_header,
    read_wdd_hashes,
    read_wdd_wdr_offsets
)

from ..RELib.wdr import read_wdr_dictionary, read_rsc_header_wdd


class WDDImporter:
    def __init__(self, filepath):
        self.filepath = filepath
        self.hashes = []
        self.wdr_offsets = []

    def load(self):
        with open(self.filepath, 'rb') as s:
            rsc_header = s.read(12)
            raw_data = s.read()

            try:
                cpu_data = zlib.decompress(raw_data)
                print("🟢 Decompression successful.")
            except zlib.error:
                print("⚪ File was not compressed - raw data used.")
                cpu_data = raw_data

            full_data = rsc_header + cpu_data
            system_mem = read_rsc_header_wdd(full_data)

            s = io.BytesIO(cpu_data)
            header = read_wdd_header(s)

            print(f"📦 WDD File: {self.filepath}")
            print(f"  Hashes: {header['hashes_count']}, Pointers: {header['wdrs_count']}")
            print(f"  Hash Offset: 0x{header['hashes_offset']:X}")
            print(f"  Pointer Offset: 0x{header['wdrs_offset']:X}")

            hash_offset = header['hashes_offset'] & 0x0FFFFFFF
            ptr_offset  = header['wdrs_offset']   & 0x0FFFFFFF

            self.hashes = read_wdd_hashes(s, hash_offset, header['hashes_count'], header['hashes_stride'])
            self.wdr_offsets = read_wdd_wdr_offsets(s, ptr_offset, header['wdrs_count'])


            for idx, raw_offset in enumerate(self.wdr_offsets):
                adjusted_offset = raw_offset & 0x0FFFFFFF
                print(f"\n🧩 WDR {idx} at 0x{raw_offset:X} (adjusted: 0x{adjusted_offset:X})")

                wdr_data = cpu_data[adjusted_offset:]
                wdr_name = f"{os.path.basename(self.filepath)}_wdr_{idx}"
                read_wdr_dictionary(self, wdr_name, wdr_data, adjusted_offset, system_mem)

                print(f"🔎 Begin reading embedded WDR {idx} at file offset 0x{adjusted_offset:X}")


class IMPORT_OT_wdd_importer(Operator, ImportHelper):
    """Import Windows Drawable Dictionary WDD (.wdd)"""
    bl_idname = "import_scene.wdd"
    bl_label = "Import WDD"
    filename_ext = ".wdd"
    filter_glob: StringProperty(default="*.wdd", options={'HIDDEN'})

    def execute(self, context):
        importer = WDDImporter(self.filepath)
        importer.load()
        return {'FINISHED'}


def menu_func_import(self, context):
    self.layout.operator(IMPORT_OT_wdd_importer.bl_idname, text="Windows Drawable Dictionary[x32](.wdd)")


def register():
    bpy.utils.register_class(IMPORT_OT_wdd_importer)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(IMPORT_OT_wdd_importer)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
