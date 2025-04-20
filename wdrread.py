# BlenDR stuff - WIP!
# Test read for .wdr format files, sure to be faulty at first.

import bpy
import struct
from bpy.props import StringProperty
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper

class IMPORT_OT_wdr_header(Operator, ImportHelper):
    bl_idname = "import_scene.wdr_header"
    bl_label = "Import WDR Header (Custom Parser)"
    bl_options = {'REGISTER', 'UNDO'}
    filename_ext = ".wdr"

    filter_glob: StringProperty(
        default="*.wdr",
        options={'HIDDEN'}
    )

    def execute(self, context):
        try:
            with open(self.filepath, "rb") as f:
                f.seek(12)  # Skip 12-byte RSC header
                header = f.read(0x50)

            def u32(offset):
                return struct.unpack_from('<I', header, offset)[0]

            def f32(offset):
                return struct.unpack_from('<f', header, offset)[0]

            def u8(offset):
                return struct.unpack_from('<B', header, offset)[0]

            print("\n🔍 WDR HEADER PARSED FROM:", self.filepath)
            print("--------------------------------------------------")
            print(f"VTable (0x00):              {u32(0x00)}")
            print(f"HeaderLength (0x04):        {u8(0x04)}")
            print(f"ShaderGroup Offset (0x08):  {hex(u32(0x08))}")
            print(f"SkeletonData Offset (0x0C): {hex(u32(0x0C))}")
            print(" ")

            print("🎯 Center (0x10)")
            print(f"  x: {f32(0x10)}")
            print(f"  y: {f32(0x14)}")
            print(f"  z: {f32(0x18)}")
            print(f"  w: {f32(0x1C)}")

            print("\n🔻 BoundsMin (0x20)")
            print(f"  x: {f32(0x20)}")
            print(f"  y: {f32(0x24)}")
            print(f"  z: {f32(0x28)}")
            print(f"  w: {f32(0x2C)}")

            print("\n🔺 BoundsMax (0x30)")
            print(f"  x: {f32(0x30)}")
            print(f"  y: {f32(0x34)}")
            print(f"  z: {f32(0x38)}")
            print(f"  w: {f32(0x3C)}")

            print("\n📦 Pointer Fields (Uint8 + Hex from final byte only)")
            print(f"  ModelCollection (0x40): {u8(0x43)} (0x{u8(0x43):02X})")
            print(f"  LOD Model 1 (0x44):     {u8(0x47)} (0x{u8(0x47):02X})")
            print(f"  LOD Model 2 (0x48):     {u8(0x4B)} (0x{u8(0x4B):02X})")
            print(f"  LOD Model 3 (0x4C):     {u8(0x4F)} (0x{u8(0x4F):02X})")
            print("--------------------------------------------------")

            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Failed to parse WDR: {e}")
            return {'CANCELLED'}

def menu_func_import(self, context):
    self.layout.operator(IMPORT_OT_wdr_header.bl_idname, text="Import WDR Header (.wdr)")

def register():
    bpy.utils.register_class(IMPORT_OT_wdr_header)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(IMPORT_OT_wdr_header)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()
