import bpy
import struct
from bpy.props import StringProperty
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper

class IMPORT_OT_wdr_reader(Operator, ImportHelper):
    bl_idname = "import_scene.wdr_reader"
    bl_label = "Read WDR"
    bl_options = {'REGISTER', 'UNDO'}
    filename_ext = ".wdr"

    filter_glob: StringProperty(default="*.wdr", options={'HIDDEN'})
    
    #Helper Functions with Stupid Names
    def read_u8(self, data, offset):
        return struct.unpack_from('<B', data, offset)[0]

    def read_u16(self, data, offset):
        return struct.unpack_from('<H', data, offset)[0]

    def read_u32(self, data, offset):
        return struct.unpack_from('<I', data, offset)[0]

    def read_f32(self, data, offset):
        return struct.unpack_from('<f', data, offset)[0]

    def read_u16_from_stream(self, stream):
        return struct.unpack('<H', stream.read(2))[0]

    def read_u32_from_stream(self, stream):
        return struct.unpack('<I', stream.read(4))[0]

    def jump_and_read_u16(self, stream, offset):
        stream.seek(offset + 12)
        return self.read_u16_from_stream(stream)

    def jump_and_read_u32(self, stream, offset):
        stream.seek(offset + 12)
        return self.read_u32_from_stream(stream)
    
    # Execute
    def execute(self, context):
        try:
            with open(self.filepath, "rb") as f:
                f.seek(12)
                header = f.read(0x94)
                model_collection = f.read(0x10)

                u8 = self.read_u8
                u16 = self.read_u16
                u32 = self.read_u32
                f32 = self.read_f32

                print("\n🔍 WDR HEADER PARSED FROM:", self.filepath)
                print("--------------------------------------------------")
                print(f"VTable (0x00):              {hex(u32(header, 0x00))}")
                print(f"HeaderLength (0x04):        {u8(header, 0x04)}")
                print(f"ShaderGroup Offset (0x08):  {hex(u32(header, 0x08))}")
                print(f"SkeletonData Offset (0x0C): {hex(u32(header, 0x0C))}\n")

                print("🎯 Center (0x10)")
                print(f"  x: {f32(header, 0x10)}")
                print(f"  y: {f32(header, 0x14)}")
                print(f"  z: {f32(header, 0x18)}")
                print(f"  w: {f32(header, 0x1C)}\n")

                print("🔻 BoundsMin (0x20)")
                print(f"  x: {f32(header, 0x20)}")
                print(f"  y: {f32(header, 0x24)}")
                print(f"  z: {f32(header, 0x28)}")
                print(f"  w: {f32(header, 0x2C)}\n")

                print("🔺 BoundsMax (0x30)")
                print(f"  x: {f32(header, 0x30)}")
                print(f"  y: {f32(header, 0x34)}")
                print(f"  z: {f32(header, 0x38)}")
                print(f"  w: {f32(header, 0x3C)}\n")

                print("📦 Pointer Fields (Uint8 + Hex from final byte only)")
                print(f"  ModelCollection (0x40): {u8(header, 0x43)} (0x{u8(header, 0x43):02X})")
                print(f"  LOD Model 1 (0x44):     {u8(header, 0x47)} (0x{u8(header, 0x47):02X})")
                print(f"  LOD Model 2 (0x48):     {u8(header, 0x4B)} (0x{u8(header, 0x4B):02X})")
                print(f"  LOD Model 3 (0x4C):     {u8(header, 0x4F)} (0x{u8(header, 0x4F):02X})\n")

                print("📐 Max Vector (0x50)")
                print(f"  x: {f32(header, 0x50)}")
                print(f"  y: {f32(header, 0x54)}")
                print(f"  z: {f32(header, 0x58)}")
                print(f"  w: {f32(header, 0x5C)}\n")

                print("📊 Object Metadata")
                print(f"  ObjectCount (0x60):     {hex(u32(header, 0x60))}")
                print(f"  Unknown (0x64):         {hex(u32(header, 0x64))}")
                print(f"  Unknown (0x68):         {hex(u32(header, 0x68))}")
                print(f"  Unknown (0x6C):         {hex(u32(header, 0x6C))}")
                print(f"  Unknown Float (0x70):   {f32(header, 0x70)}")

                print(f"  Unknown (0x74–0x7F):")
                print(f"    [0x74]: {hex(u32(header, 0x74))}")
                print(f"    [0x78]: {hex(u32(header, 0x78))}")
                print(f"    [0x7C]: {hex(u32(header, 0x7C))}\n")

                print("🎯 2DFX Section")
                print(f"  2DFX Offset (0x80):     {hex(u32(header, 0x80))}")
                print(f"  2DFX Count (0x84):      {u16(header, 0x84)}")
                print(f"  2DFX Size (0x86):       {u16(header, 0x86)}")

                print("🔸 Unassigned 8b (0x88):")
                print(f"  {header[0x88:0x90].hex().upper()}")

                print("🔚 End of Header (0x90):")
                print(f"  {hex(u32(header, 0x90))}")
                print("--------------------------------------------------\n") # Rubbish - but we know what to do now
                print("\n------------------------------------------------")
                print("\n ...BEGIN READING MODELCOLLECTION SECTION...")
                print("--------------------------------------------------\n")
                
                # Logic for model collection pointer
                f.seek(0x4C)
                ptr_to_modelcollection_ptr = self.read_u16_from_stream(f)
                print("📂 Model Collection Section")
                print(f"  Pointer to ModelCollection pointer (0x40): {hex(ptr_to_modelcollection_ptr)}")

                model_section_u16 = self.jump_and_read_u16(f, ptr_to_modelcollection_ptr)
                print(f"  Model Offset Value (0x00): {hex(model_section_u16)}")
                print("--------------------------------------------------\n")

                next_value_u16 = self.jump_and_read_u16(f, model_section_u16)
                print(f"  Value at Model Offset {hex(model_section_u16)}:       {hex(next_value_u16)}")
                print("--------------------------------------------------\n")
                print("\n------------------------------------------------")
                print("\n ...BEGIN READING MODEL SECTION...")
                print("--------------------------------------------------\n")
                

                model_vtable = self.jump_and_read_u32(f, next_value_u16)
                print(f"📌 Jumped to Offset (0x{next_value_u16:X})")
                print(f"  Model VTable (0x{next_value_u16:X}): {hex(model_vtable)}")
                print("--------------------------------------------------\n")

                geometry_collection_ptr = self.read_u16_from_stream(f)
                print(f"📂 Geometry Collection Pointer (0x00): {hex(geometry_collection_ptr)}")
                

                geometry_collection_ptrs = []
      

                # Seek to the next 4 bytes after the Geometry Collection Pointer
                number_of_model_pointers_1 = self.read_u16_from_stream(f)
                number_of_model_pointers_2 = self.read_u16_from_stream(f)
                print(f"📖 Number of Model Pointers 1 (0x{number_of_model_pointers_1 + 2}): {hex(number_of_model_pointers_1)}")
                print(f"📖 Number of Model Pointers 2 (0x{number_of_model_pointers_2 + 2:X}): {hex(number_of_model_pointers_2)}")

                
                simplearray_vector_ptr = self.read_u32_from_stream(f)
                
                print(f"Pointer to SimpleArray(Vector4) (0x{simplearray_vector_ptr}): {hex(simplearray_vector_ptr)}")
                
                f.seek(2, 1)
                
                simplearray_integer_ptr = self.read_u16_from_stream(f)
                
                print(f"Pointer to SimpleArray(Integer) (0x{simplearray_integer_ptr}): {hex(simplearray_integer_ptr)}")
            
                f.seek(2, 1)
            
                # Read Unknown1 (2 bytes)
                unknown1 = self.read_u16_from_stream(f)
                print(f"🔍 Model Unknown1 (0x14): {hex(unknown1)}")

                # Read Unknown2 (2 bytes)
                unknown2 = self.read_u16_from_stream(f)
                print(f"🔍 Model Unknown2 (0x16): {hex(unknown2)}")

                # Read Unknown3 (2 bytes)
                unknown3 = self.read_u16_from_stream(f)
                print(f"🔍 Model Unknown3 (0x18): {hex(unknown3)}")

                # Read GeometryCount (2 bytes)
                geometry_count = self.read_u16_from_stream(f)
                print(f"🔢 GeometryCount (0x1A): {geometry_count}")

                # Read Padding (4 bytes)
                padding = self.read_u32_from_stream(f)
                print(f"🧹 Padding (0x1C): {hex(padding)}")
                
                f.seek(geometry_collection_ptr)
                print(f" Moved to: {hex(geometry_collection_ptr)}")
                
                geometry_collection_ptrs = []

                # Read the pointer stored at geometry_collection_ptr
                true_geometry_array_ptr_1 = self.jump_and_read_u16(f, geometry_collection_ptr)
                geometry_collection_ptrs.append(true_geometry_array_ptr_1)
                print(f"📍 Geometry Array Pointer read at {hex(geometry_collection_ptr)}: {hex(true_geometry_array_ptr_1)}")

                f.seek(2, 1)

                # Read the pointer stored at geometry_collection_ptr
                true_geometry_array_ptr_2 = self.read_u16_from_stream(f)
                geometry_collection_ptrs.append(true_geometry_array_ptr_2)
                print(f"📍 Geometry Array Pointer read at {hex(geometry_collection_ptr + 4)}: {hex(true_geometry_array_ptr_2)}")    
                    
                for i in range(geometry_count):
                    ptr = self.jump_and_read_u16(f, geometry_collection_ptr + (i * 4))
                    geometry_collection_ptrs.append(ptr)
                    print(f"📍 Geometry Array Pointer {i} read at {hex(geometry_collection_ptr + (i * 4))}: {hex(ptr)}")    
                    
                print("--------------------------------------------------\n")
                print("\n------------------------------------------------")
                print("\n ...BEGIN READING GEOMETRIES...")
                print("--------------------------------------------------\n")
                
                
                
                for i, geometry_ptr in enumerate(geometry_collection_ptrs):
                    print(f"\n🚀 Reading Geometry {i} at {hex(geometry_ptr)}")

                    geo_vtable = self.jump_and_read_u32(f, geometry_ptr)
                    print(f"  Geometry VTable: {hex(geo_vtable)}")

                    geometry_unk_1 = self.read_u32_from_stream(f)
                    print(f"  Geometry Unknown 1: {geometry_unk_1}")

                    geometry_unk_2 = self.read_u32_from_stream(f)
                    print(f"  Geometry Unknown 2: {geometry_unk_2}")

                    vertex_buffer_ptr = self.read_u16_from_stream(f)
                    print(f"  Vertex Buffer Pointer: {hex(vertex_buffer_ptr)}")

                    f.seek(2, 1)

                    geometry_unk_3 = self.read_u32_from_stream(f)
                    print(f"  Geometry Unknown 3: {geometry_unk_3}")

                    geometry_unk_4 = self.read_u32_from_stream(f)
                    print(f"  Geometry Unknown 4: {geometry_unk_4}")

                    geometry_unk_5 = self.read_u32_from_stream(f)
                    print(f"  Geometry Unknown 5: {geometry_unk_5}")

                    index_buffer_ptr = self.read_u16_from_stream(f)
                    print(f"  Index Buffer Pointer: {hex(index_buffer_ptr)}")
                    
                    f.seek(2, 1) # What a bother - need to avoid doing this.

                    geometry_unk_6 = self.read_u32_from_stream(f)
                    print(f"  Geometry Unknown 6: {geometry_unk_6}")

                    geometry_unk_7 = self.read_u32_from_stream(f)
                    print(f"  Geometry Unknown 7: {geometry_unk_7}")

                    geometry_unk_8 = self.read_u32_from_stream(f)
                    print(f"  Geometry Unknown 8: {geometry_unk_8}")

                    index_count = self.read_u32_from_stream(f)
                    print(f"  Geometry Index Count: {index_count}")

                    face_count = self.read_u32_from_stream(f)
                    print(f"  Geometry Face Count: {face_count}")

                    vertex_count = self.read_u16_from_stream(f)
                    print(f"  Geometry Vertex Count: {vertex_count}")

                    geo_primitive_type = self.read_u16_from_stream(f)
                    print(f"  Primitive Type: {geo_primitive_type}")

                    geometry_unk_9 = self.read_u32_from_stream(f)
                    print(f"  Geometry Unknown 9: {geometry_unk_9}")

                    vertex_stride = self.read_u16_from_stream(f)
                    print(f"  Vertex Stride: {vertex_stride}")

                    geometry_unk_10 = self.read_u16_from_stream(f)
                    print(f"  Geometry Unknown 10: {geometry_unk_10}")

                    geometry_unk_11 = self.read_u32_from_stream(f)
                    print(f"  Geometry Unknown 11: {geometry_unk_11}")

                    geometry_unk_12 = self.read_u32_from_stream(f)
                    print(f"  Geometry Unknown 12: {geometry_unk_12}")

                    geometry_unk_13 = self.read_u32_from_stream(f)
                    print(f"  Geometry Unknown 13: {geometry_unk_13}")

                    print("--------------------------------------------------\n")
                    print("\n------------------------------------------------")
                    print("\n ...GEOMETRIES SUCCESSFULLY READ...")
                    print("--------------------------------------------------\n")
                    

            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Failed to parse WDR: {e}")
            return {'CANCELLED'}

def menu_func_import(self, context):
    self.layout.operator(IMPORT_OT_wdr_reader.bl_idname, text="Read WDR (.wdr)")

def register():
    bpy.utils.register_class(IMPORT_OT_wdr_reader)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(IMPORT_OT_wdr_reader)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()