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

import io
import os
import bpy
import zlib
import struct
from bpy.types import Operator
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

#######################################################
class IMPORT_OT_wdr_reader(Operator, ImportHelper):
    bl_idname = "import_scene.wdr_reader"
    bl_label = "Import WDR(.wdr)"
    bl_options = {'REGISTER', 'UNDO'}
    filename_ext = ".wdr"
    #######################################################
    filter_glob: StringProperty(default="*.wdr", options={'HIDDEN'})

    
    #Helper Functions with Stupid Names
    def read_u8(self, data, offset):
        return struct.unpack_from('<B', data, offset)[0]
    #######################################################
    def read_u16(self, data, offset):
        return struct.unpack_from('<H', data, offset)[0]
    #######################################################
    def read_u32(self, data, offset):
        return struct.unpack_from('<I', data, offset)[0]
    #######################################################
    def read_f32(self, data, offset):
        return struct.unpack_from('<f', data, offset)[0]
    #######################################################
    def read_u16_from_stream(self, stream):
        return struct.unpack('<H', stream.read(2))[0]
    #######################################################
    def read_u32_from_stream(self, stream):
        return struct.unpack('<I', stream.read(4))[0]
    #######################################################
    def jump_and_read_u16(self, stream, offset):
        stream.seek(offset + 12)
        return self.read_u16_from_stream(stream)
    #######################################################
    def jump_and_read_u32(self, stream, offset):
        stream.seek(offset + 12)
        return self.read_u32_from_stream(stream)
    #######################################################
    def execute(self, context):
        #######################################################
        def read_u8(s): return struct.unpack('<B', s.read(1))[0]
        #######################################################
        def read_u16(s): return struct.unpack('<H', s.read(2))[0]
        #######################################################
        def read_u32(s): return struct.unpack('<I', s.read(4))[0]
        #######################################################
        def read_f32(s): return struct.unpack('<f', s.read(4))[0]
        #######################################################
    
        def read_data_offset(s):
            value = read_u32(s)
            nibble = value >> 28
            if nibble in (5, 6):
                return value & 0x0FFFFFFF
            elif value == 0:
                return 0
            else:
                return value & 0x0FFFFFFF
    
        try:
            filename = os.path.basename(self.filepath)
            print(f"\n ...BEGIN READING FOR {filename}...\n")

            with open(self.filepath, "rb") as f:
                # Read RSC Header
                magic_dword = f.read(3)  # 'RSC'
                file_type = f.read(1)  # e.g., 05
                version = struct.unpack('<I', f.read(4))[0] # Version 110 for IV
                flags = struct.unpack('<I', f.read(4))[0] # Physical + graphics size

                #######################################################
                def get_memory_sizes(filename, flags):  # Credits to utopiadeferred for memory size functions
                    total_mem_size = get_total_mem_size(flags)
                    system_mem_size = get_system_mem_size(flags)
                    graphics_mem_size = get_graphics_mem_size(flags)

                    print(f"Total Memory Size: {total_mem_size} bytes, System Memory Size: {system_mem_size} bytes, Graphics Memory Size: {graphics_mem_size} bytes.")
                #######################################################
                def get_total_mem_size(flags: int) -> int:
                    return get_system_mem_size(flags) + get_graphics_mem_size(flags)
                #######################################################
                def get_system_mem_size(flags: int) -> int:
                    return (flags & 0x7FF) << (((flags >> 11) & 0xF) + 8)   # Bitshift to get size
                #######################################################
                def get_graphics_mem_size(flags: int) -> int:
                    return ((flags >> 15) & 0x7FF) << (((flags >> 26) & 0xF) + 8)
                #######################################################
                def get_graphics_mem_size(flags: int) -> int:
                    return ((flags >> 15) & 0x7FF) << (((flags >> 26) & 0xF) + 8)
                #######################################################
                system_mem = get_system_mem_size(flags)
                graphics_mem = get_graphics_mem_size(flags)
                total_mem_size = system_mem + graphics_mem

                get_memory_sizes(filename, flags)
                
                print("--------------------------------------------------")
                print("\n ... READING RSC HEADER ...")
                print("--------------------------------------------------")
                print(f"  Magic DWORD:         {magic_dword.decode(errors='ignore')}")
                print(f"  File Type:     {file_type.hex()}")
                print(f"  Version:       {version}")
                print(f"  Flags:         {hex(flags)}")
                print(f"  System Mem:    {system_mem} bytes")
                print(f"  Graphics Mem:  {graphics_mem} bytes")
                print(f"  Total Mem:     {total_mem_size} bytes (for pointer fixup)")
                
                
                # Read CPU data
                cpu_data = f.read()

                # Decompress CPU data
                try:
                    print("\n🗜️  Attempting decompression...")
                    cpu_data = zlib.decompress(cpu_data)
                    print("🟢 Decompression successful.")
                except zlib.error:
                    print("⚪ File is not compressed, using raw data.")

                s = io.BytesIO(cpu_data)


                print("--------------------------------------------------")
                print("\n ... READING WDR HEADER...")
                print("--------------------------------------------------")
                vtable = read_u32(s)
                header_length = read_u8(s)
                s.read(3)
                shadergroup_offset = read_data_offset(s)
                skeleton_offset = read_data_offset(s)
                cx, cy, cz, cw = read_f32(s), read_f32(s), read_f32(s), read_f32(s)
                minx, miny, minz, minw = read_f32(s), read_f32(s), read_f32(s), read_f32(s)
                maxx, maxy, maxz, maxw = read_f32(s), read_f32(s), read_f32(s), read_f32(s)

                s.seek(0x43)
                model_ptr = read_u8(s)
                s.seek(0x47)
                lod1 = read_u8(s)
                s.seek(0x4B)
                lod2 = read_u8(s)
                s.seek(0x4F)
                lod3 = read_u8(s)

                s.seek(0x50)
                maxvx, maxvy, maxvz, maxvw = read_f32(s), read_f32(s), read_f32(s), read_f32(s)

                s.seek(0x60)
                obj_count = read_u32(s)
                
                object_vertices = [[] for _ in range(obj_count)]
                object_indices = [[] for _ in range(obj_count)]
                geometry_counts = []
                geometries_read = 0
                current_object = 0
                
                unk64, unk68, unk6c = read_u32(s), read_u32(s), read_u32(s)
                unk70 = read_f32(s)
                unk74, unk78, unk7c = read_u32(s), read_u32(s), read_u32(s)

                fx_offset = read_data_offset(s)
                fx_count = read_u16(s)
                fx_size = read_u16(s)
                raw88 = s.read(8)
                end_header = read_u32(s)

                print("\n🔥 WDR HEADER:")
                print(f"  VTable:        0x{vtable:08X}")
                print(f"  ShaderGroup:   0x{shadergroup_offset:08X}")
                print(f"  SkeletonData:  0x{skeleton_offset:08X}")
                print(f"  Center:        ({cx}, {cy}, {cz}, {cw})")
                print(f"  Min:           ({minx}, {miny}, {minz}, {minw})")
                print(f"  Max:           ({maxx}, {maxy}, {maxz}, {maxw})")
                print(f"  ModelPtrs:     MC=0x{model_ptr:X}, LOD1=0x{lod1:X}, LOD2=0x{lod2:X}, LOD3=0x{lod3:X}")
                print(f"  Max Vector:    ({maxvx}, {maxvy}, {maxvz}, {maxvw})")
                print(f"  ObjCount:      {obj_count}")
                print(f"  Unknowns:      {hex(unk64)}, {hex(unk68)}, {hex(unk6c)}, {unk70}")
                print(f"                {hex(unk74)}, {hex(unk78)}, {hex(unk7c)}")
                print(f"  2DFX Offset:   0x{fx_offset:08X}, Count: {fx_count}, Size: {fx_size}")
                print(f"  Reserved:      {' '.join(f'{b:02X}' for b in raw88)}")
                print(f"  End Header:    0x{end_header:08X}")

                print("--------------------------------------------------")
                print("\n ... READING MODELCOLLECTION...")
                print("--------------------------------------------------")
                s.seek(0x40)
                model_collection_offset = read_data_offset(s)
                s.seek(model_collection_offset)
                model_pointer_offset_ptr = read_data_offset(s)
                num_ptrs_1 = read_u16(s)
                num_ptrs_2 = read_u16(s)
                padding_1 = read_u32(s)
                padding_2 = read_u32(s)

                print("\n📦 Model Collection:")
                print(f"  Collection Offset:    0x{model_collection_offset:08X}")
                print(f"  Model Pointer Offset: 0x{model_pointer_offset_ptr:08X}")
                print(f"  Pointer Counts:       {num_ptrs_1}, {num_ptrs_2}")
                print(f"  Padding:              0x{padding_1:08X}, 0x{padding_2:08X}")

                s.seek(model_pointer_offset_ptr)
                model_offset = read_data_offset(s)

                print("--------------------------------------------------")
                print("\n ... READING MODEL SECTION...")
                print("--------------------------------------------------")
                s.seek(model_offset)
                model_vtable = read_u32(s)
                geometry_collection_offset = read_data_offset(s)
                number_of_geo_ptrs = read_u16(s)
                number_of_geometries = read_u16(s)
                vector_array_offset = read_data_offset(s)
                material_array_offset = read_data_offset(s)
                unk1 = read_u16(s)
                unk2 = read_u16(s)
                unk3 = read_u16(s)
                geometry_count = read_u16(s)
                model_padding = read_u32(s)

                print("\n🔷 Model Block:")
                print(f"  VTable:             0x{model_vtable:08X}")
                print(f"  Geometry Ptr:       0x{geometry_collection_offset:08X}")
                print(f"  Number of Geometry Ptrs:       {number_of_geo_ptrs}")
                print(f"  Number of Geometries:          {number_of_geometries}")
                print(f"  Vector4 Array Ptr:  0x{vector_array_offset:08X}")
                print(f"  Material Array Ptr: 0x{material_array_offset:08X}")
                print(f"  Unknowns:           {unk1}, {unk2}, {unk3}")
                print(f"  Geometry Count:     {geometry_count}")
                print(f"  Padding:            0x{model_padding:08X}")

                print("--------------------------------------------------")
                print("\n ... READING GEOMETRY...")
                print("--------------------------------------------------")
                print("\n📏 Geometries:")
                s.seek(geometry_collection_offset)
                geometry_offsets = [read_data_offset(s) for _ in range(number_of_geometries)]

                total_vertex_count_so_far = 0

                for i, geom_offset in enumerate(geometry_offsets):
                    s.seek(geom_offset)
                    geo_vtable = read_u32(s)
                    unk1 = read_u32(s)
                    unk2 = read_u32(s)
                    vertex_buffer_ptr = read_data_offset(s)
                    unk3 = read_u32(s)
                    unk4 = read_u32(s)
                    unk5 = read_u32(s)
                    index_buffer_ptr = read_data_offset(s)
                    unk6 = read_u32(s)
                    unk7 = read_u32(s)
                    unk8 = read_u32(s)
                    index_count = read_u32(s)
                    face_count = read_u32(s)
                    vertex_count = read_u16(s)
                    primitive_type = read_u16(s)
                    unk9 = read_u32(s)
                    vertex_stride = read_u16(s)
                    
                    vertex_data_length = vertex_count * vertex_stride
                    print(f"    Vertex Data Length: {vertex_data_length} bytes")

                    unk10 = read_u16(s)
                    unk11 = read_u32(s)
                    unk12 = read_u32(s)
                    unk13 = read_u32(s)
                    padding = read_u32(s)

                    print(f"\n  Geometry {i} Offset: 0x{geom_offset:08X}")
                    print(f"    VTable:          0x{geo_vtable:08X}")
                    print(f"    Vertex Buffer:   0x{vertex_buffer_ptr:08X}")
                    print(f"    Index Buffer:    0x{index_buffer_ptr:08X}")
                    print(f"    Index Count:     {index_count}")
                    print(f"    Face Count:      {face_count}")
                    print(f"    Vertex Count:    {vertex_count}")
                    print(f"    Primitive Type:  {primitive_type}")
                    print(f"    Vertex Stride:   {vertex_stride}")
                    print(f"    Padding:         0x{padding:08X}")

                    print("--------------------------------------------------")
                    print("\n ... READING VERTEX BUFFER...")
                    print("--------------------------------------------------")
                    s.seek(vertex_buffer_ptr)
                    vb_vtable = read_u32(s)
                    vb_vert_count = read_u16(s)
                    vb_unknown1 = read_u16(s)
                    vb_data_offset1 = read_data_offset(s)
                    vb_stride = read_u32(s)
                    vb_decl_offset = read_data_offset(s)
                    vb_unknown2 = read_u32(s)
                    vb_data_offset2 = read_data_offset(s)
                    vb_unknown3 = read_u32(s)

                    print(f"    🔹 Vertex Buffer:")
                    print(f"      VTable:        0x{vb_vtable:08X}")
                    print(f"      Vertex Count:  {vb_vert_count}")
                    print(f"      Stride:        {vb_stride}")
                    print(f"      Data Offset 1: 0x{vb_data_offset1:08X}")
                    print(f"      Decl Offset:   0x{vb_decl_offset:08X}")
                    print(f"      Data Offset 2: 0x{vb_data_offset2:08X}")

                    print("--------------------------------------------------")
                    print("\n ... READING INDEX BUFFER...")
                    print("--------------------------------------------------")
                    s.seek(index_buffer_ptr)
                    ib_vtable = read_u32(s)
                    ib_index_count = read_u32(s)
                    ib_data_offset = read_data_offset(s)
                    ib_unknown1 = read_u32(s)

                    print(f"    🔸 Index Buffer:")
                    print(f"      VTable:        0x{ib_vtable:08X}")
                    print(f"      Index Count:   {ib_index_count}")
                    print(f"      Data Offset:   0x{ib_data_offset:08X}")
                    print(f"      Unknown 1:   0x{ib_unknown1:08X}")

                    print("--------------------------------------------------")
                    print("\n ... READING VERTEX DECLARATION...")
                    print("--------------------------------------------------")
                    s.seek(vb_decl_offset)
                    usage_flags = read_u32(s)
                    stride = read_u16(s)
                    decoder = read_u8(s)
                    decl_type = read_u8(s)
                    unk1 = read_u32(s)
                    unk2 = read_u32(s)

                    print(f"    📄 Vertex Declaration:")
                    print(f"      Usage Flags:   0x{usage_flags:08X}")
                    print(f"      Stride:        {stride}")
                    print(f"      Decoder:       {decoder}")
                    print(f"      Type:          {decl_type}")
                    print(f"      Unknown 1:     0x{unk1:08X}")
                    print(f"      Unknown 2:     0x{unk2:08X}")
                    
                    print("--------------------------------------------------")
                    print("\n ... READING VERTEX DATA...")
                    print("--------------------------------------------------")
                    real_vtx_offset = vb_data_offset1
                    s.seek(real_vtx_offset)
                    data = memoryview(cpu_data)
                    def read_f32_buf(buf, offset): return struct.unpack_from('<f', buf, offset)[0]
                    def read_u32_buf(buf, offset): return struct.unpack_from('<I', buf, offset)[0]
                    def read_u8_buf(buf, offset): return struct.unpack_from('<B', buf, offset)[0]

                    verts = []
                    

                    
                    for v in range(vb_vert_count):
                        vb_base = real_vtx_offset + system_mem  # Thanks to Utopia for offset + stride + physical size
                        if stride == 36:
                            base = vb_base + (v * vertex_stride)
                            px = read_f32_buf(data, base + 0)
                            py = read_f32_buf(data, base + 4)
                            pz = read_f32_buf(data, base + 8)
                            nx = read_f32_buf(data, base + 12)
                            ny = read_f32_buf(data, base + 16)
                            nz = read_f32_buf(data, base + 20)
                            r = read_u8_buf(data, base + 24)
                            g = read_u8_buf(data, base + 25)
                            b = read_u8_buf(data, base + 26)
                            a = read_u8_buf(data, base + 27)
                            u = read_f32_buf(data, base + 28)
                            v_ = read_f32_buf(data, base + 32)
                        elif stride == 52:
                            tx = read_f32_buf(data, base + 36)
                            ty = read_f32_buf(data, base + 40)
                            tz = read_f32_buf(data, base + 44)
                            tw = read_f32_buf(data, base + 48)


                        print(f"  Vertex {v}: Pos=({px:.5f}, {py:.5f}, {pz:.5f}) "
                              f"Normal=({nx:.3f}, {ny:.3f}, {nz:.3f}) "
                              f"Color=({r:02X}, {g:02X}, {b:02X}, {a:02X}) "
                              f"UV=({u:.5f}, {v_:.5f})")
                              
                        verts.append((px, py, pz))
                        
                    print("--------------------------------------------------")
                    print("\n ... READING INDEX DATA...")
                    print("--------------------------------------------------")
                    s.seek(index_buffer_ptr)
                    ib_vtable = read_u32(s)            # 0x00
                    ib_index_count = read_u32(s)       # 0x04
                    ib_data_offset = read_data_offset(s)  # 0x08
                    ib_unknown1 = read_u32(s)          # 0x0C
                    ib_padding = s.read(0x30)          # 0x10 - 0x3F (padding)

                    print(f"    🔸 Full IndexBuffer Read:")
                    print(f"      VTable:       0x{ib_vtable:08X}")
                    print(f"      Index Count:  {ib_index_count}")
                    print(f"      Data Offset:  0x{ib_data_offset:08X}")
                    print(f"      Unknown 1:    0x{ib_unknown1:08X}")
                    print(f"      Padding:      {' '.join(f'{b:02X}' for b in ib_padding)}")

                    indices = []
                    index_data_offset = ib_data_offset + system_mem  # Read like VertexBuffer/VertexData?
                    print(f"     New Data Offset:  0x{index_data_offset:08X}")
                    for tri_index in range(ib_index_count // 3):  # Tristrips
                        base = index_data_offset + (tri_index * 6)

                        offset_i0 = base + 0
                        offset_i1 = base + 2
                        offset_i2 = base + 4


                        print(f"🔍 Triangle {tri_index}: reading indices from offsets {offset_i0:#X}, {offset_i1:#X}, {offset_i2:#X}")

                        i0 = struct.unpack_from('<H', data, offset_i0)[0]
                        i1 = struct.unpack_from('<H', data, offset_i1)[0]
                        i2 = struct.unpack_from('<H', data, offset_i2)[0]
                        indices.append((i0, i1, i2))

                        print(f"    Indices = ({i0}, {i1}, {i2})")

                        
                        object_vertices[current_object] = verts
                        object_indices[current_object] = indices


                    print(f"      ✅ Read {len(indices)} triangle faces from index data.")
                    
                    for i, verts in enumerate(object_vertices):
                        if not verts:
                            continue

                        base_name = os.path.splitext(filename)[0]
                        mesh = bpy.data.meshes.new(f"{base_name}_Mesh_{i}")
                        obj = bpy.data.objects.new(f"{base_name}_Object_{i}", mesh)

                        bpy.context.collection.objects.link(obj)

                        tris = indices
                        mesh.from_pydata(verts, [], tris)
                        mesh.update()

                        print(f"🚀 Created {base_name}_Object_{i} with {len(verts)} vertices and {len(tris)} triangles.")

            
            return {'FINISHED'}

                
        except Exception as e:
            self.report({'ERROR'}, f"Failed to parse WDR: {e}")
            return {'CANCELLED'}
    #######################################################
def menu_func_import(self, context):
    self.layout.operator(IMPORT_OT_wdr_reader.bl_idname, text="Windows Drawable[x32](.WDR)")

def register():
    bpy.utils.register_class(IMPORT_OT_wdr_reader)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(IMPORT_OT_wdr_reader)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()
