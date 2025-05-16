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
import struct

from io import BytesIO
from bpy.types import Operator
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

from ..REutils import rage_iv_helpers as rh

#######################################################
class IMPORT_OT_wdr_reader(Operator, ImportHelper):
    bl_idname = "import_scene.wdr_reader"
    bl_label = "Import WDR(.wdr)"
    bl_options = {'REGISTER', 'UNDO'}
    filename_ext = ".wdr"
    #######################################################
    filter_glob: StringProperty(default="*.wdr", options={'HIDDEN'})

    def execute(self, context):
    
        try:
            filename = os.path.basename(self.filepath)
            print(f"\n ...BEGIN READING FOR {filename}...\n")

            with open(self.filepath, "rb") as f:
                # Read RSC Header
                magic_dword = f.read(3)  # 'RSC'
                file_type = f.read(1)  # e.g., 05 for IV
                version = struct.unpack('<I', f.read(4))[0] # Version 110 for IV
                flags = struct.unpack('<I', f.read(4))[0] # Physical + graphics size

                #######################################################
                def get_memory_sizes(filename, flags):  # Thanks to Utopiadeferred for memory size functions
                    total_mem_size = get_total_mem_size(flags)
                    system_mem_size = get_system_mem_size(flags)
                    graphics_mem_size = get_graphics_mem_size(flags)

                    print(f"Total Memory Size: {total_mem_size} bytes, System Memory Size: {system_mem_size} bytes, Graphics Memory Size: {graphics_mem_size} bytes.")
                #######################################################
                def get_total_mem_size(flags: int) -> int:
                    return get_system_mem_size(flags) + get_graphics_mem_size(flags)
                #######################################################
                def get_system_mem_size(flags: int) -> int:
                    return (flags & 0x7FF) << (((flags >> 11) & 0xF) + 8)   # Bitmasking to get size
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
                print("\n ... READING RESOURCE(RSC) HEADER ...")
                print("--------------------------------------------------")
                print(f"  Magic DWORD:         {magic_dword.decode(errors='ignore')}")  # RSC
                print(f"  File Type:     {file_type.hex()}")                            # IV = RSC5
                print(f"  Version:       {version}")                                    # IV = 110                      
                print(f"  Flags:         {hex(flags)}")
                print(f"  System Mem:    {system_mem} bytes")                           # Physical size
                print(f"  Graphics Mem:  {graphics_mem} bytes")                         # Data size
                print(f"  Total Mem:     {total_mem_size} bytes (for pointer fixup)")
                
                
                # Read CPU data
                cpu_data = f.read()

                # Decompress CPU data
                try:
                    print("\n!!  Attempting decompression...")
                    cpu_data = zlib.decompress(cpu_data)        # IV models = best Zlib compression
                    print("🟢 Decompression successful.")
                except zlib.error:
                    print("⚪ File was not compressed - raw data used.")                # If not Zlib compressed

                s = io.BytesIO(cpu_data)    


                print("--------------------------------------------------")
                print("\n ... READING WDR HEADER...")
                print("--------------------------------------------------")
                vtable = rh.read_u32(s)
                header_length = rh.read_u8(s)
                s.read(3)
                shadergroup_offset = rh.read_data_offset(s)
                skeleton_offset = rh.read_data_offset(s)
                cx, cy, cz, cw = rh.read_f32(s), rh.read_f32(s), rh.read_f32(s), rh.read_f32(s)
                minx, miny, minz, minw = rh.read_f32(s), rh.read_f32(s), rh.read_f32(s), rh.read_f32(s)
                maxx, maxy, maxz, maxw = rh.read_f32(s), rh.read_f32(s), rh.read_f32(s), rh.read_f32(s)

                s.seek(0x43)
                model_ptr = rh.read_u8(s)
                s.seek(0x47)
                lod1 = rh.read_u8(s)
                s.seek(0x4B)
                lod2 = rh.read_u8(s)
                s.seek(0x4F)
                lod3 = rh.read_u8(s)

                s.seek(0x50)
                maxvx, maxvy, maxvz, maxvw = rh.read_f32(s), rh.read_f32(s), rh.read_f32(s), rh.read_f32(s)

                s.seek(0x60)
                obj_count = rh.read_u32(s)
                
                object_vertices = [[] for _ in range(obj_count)]
                object_indices = [[] for _ in range(obj_count)]
                geometry_counts = []
                geometries_read = 0
                current_object = 0
                
                unk64, unk68, unk6c = rh.read_u32(s), rh.read_u32(s), rh.read_u32(s)
                unk70 = rh.read_f32(s)
                unk74, unk78, unk7c = rh.read_u32(s), rh.read_u32(s), rh.read_u32(s)

                fx_offset = rh.read_data_offset(s)
                fx_count = rh.read_u16(s)
                fx_size = rh.read_u16(s)
                raw88 = s.read(8)
                end_header = rh.read_u32(s)

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
                model_collection_offset = rh.read_data_offset(s)
                s.seek(model_collection_offset)
                model_pointer_offset_ptr = rh.read_data_offset(s)
                num_ptrs_1 = rh.read_u16(s)
                num_ptrs_2 = rh.read_u16(s)
                padding_1 = rh.read_u32(s)
                padding_2 = rh.read_u32(s)

                print("\n📦 Model Collection:")
                print(f"  Collection Offset:    0x{model_collection_offset:08X}")
                print(f"  Model Pointer Offset: 0x{model_pointer_offset_ptr:08X}")
                print(f"  Pointer Counts:       {num_ptrs_1}, {num_ptrs_2}")
                print(f"  Padding:              0x{padding_1:08X}, 0x{padding_2:08X}")

                s.seek(model_pointer_offset_ptr)
                model_offset = rh.read_data_offset(s)

                print("--------------------------------------------------")
                print("\n ... READING MODEL SECTION...")
                print("--------------------------------------------------")
                s.seek(model_offset)
                model_vtable = rh.read_u32(s)
                geometry_collection_offset = rh.read_data_offset(s)
                number_of_geo_ptrs = rh.read_u16(s)
                number_of_geometries = rh.read_u16(s)
                vector_array_offset = rh.read_data_offset(s)
                material_array_offset = rh.read_data_offset(s)
                unk1 = rh.read_u16(s)
                unk2 = rh.read_u16(s)
                unk3 = rh.read_u16(s)
                geometry_count = rh.read_u16(s)
                model_padding = rh.read_u32(s)

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
                geometry_offsets = [rh.read_data_offset(s) for _ in range(number_of_geometries)]

                total_vertex_count_so_far = 0

                for i, geom_offset in enumerate(geometry_offsets):
                    s.seek(geom_offset)
                    geo_vtable = rh.read_u32(s)
                    unk1 = rh.read_u32(s)
                    unk2 = rh.read_u32(s)
                    vertex_buffer_ptr = rh.read_data_offset(s)
                    unk3 = rh.read_u32(s)
                    unk4 = rh.read_u32(s)
                    unk5 = rh.read_u32(s)
                    index_buffer_ptr = rh.read_data_offset(s)
                    unk6 = rh.read_u32(s)
                    unk7 = rh.read_u32(s)
                    unk8 = rh.read_u32(s)
                    index_count = rh.read_u32(s)
                    face_count = rh.read_u32(s)
                    vertex_count = rh.read_u16(s)
                    primitive_type = rh.read_u16(s)
                    unk9 = rh.read_u32(s)
                    vertex_stride = rh.read_u16(s)
                    
                    vertex_data_length = vertex_count * vertex_stride
                    print(f"    Vertex Data Length: {vertex_data_length} bytes")

                    unk10 = rh.read_u16(s)
                    unk11 = rh.read_u32(s)
                    unk12 = rh.read_u32(s)
                    unk13 = rh.read_u32(s)
                    padding = rh.read_u32(s)

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
                    vb_vtable = rh.read_u32(s)
                    vb_vert_count = rh.read_u16(s)
                    vb_unknown1 = rh.read_u16(s)
                    vb_data_offset1 = rh.read_data_offset(s)
                    vb_stride = rh.read_u32(s)
                    vb_decl_offset = rh.read_data_offset(s)
                    vb_unknown2 = rh.read_u32(s)
                    vb_data_offset2 = rh.read_data_offset(s)
                    vb_unknown3 = rh.read_u32(s)

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
                    ib_vtable = rh.read_u32(s)
                    ib_index_count = rh.read_u32(s)
                    ib_data_offset = rh.read_data_offset(s)
                    ib_unknown1 = rh.read_u32(s)

                    print(f"    🔸 Index Buffer:")
                    print(f"      VTable:        0x{ib_vtable:08X}")
                    print(f"      Index Count:   {ib_index_count}")
                    print(f"      Data Offset:   0x{ib_data_offset:08X}")
                    print(f"      Unknown 1:   0x{ib_unknown1:08X}")

                    print("--------------------------------------------------")
                    print("\n ... READING VERTEX DECLARATION...")
                    print("--------------------------------------------------")
                    s.seek(vb_decl_offset)
                    usage_flags = rh.read_u32(s)
                    stride = rh.read_u16(s)
                    decoder = rh.read_u8(s)
                    decl_type = rh.read_u8(s)
                    unk1 = rh.read_u32(s)
                    unk2 = rh.read_u32(s)

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

                    verts = []

                    stride_map = {
                        28: rh.read_stride28,
                        36: rh.read_stride36,
                        44: rh.read_stride44,
                        52: rh.read_stride52,
                        60: rh.read_stride60,
                        68: rh.read_stride68,
                    }

                    stride_func = stride_map.get(stride)
                    if stride_func is None:
                        raise ValueError(f"Unsupported vertex stride: {stride}")

                    verts = []
                    vertex_data_start = real_vtx_offset + system_mem
                    vertex_buffer_slice = cpu_data[vertex_data_start : vertex_data_start + (vb_vert_count * stride)]
                    vert_stream = BytesIO(vertex_buffer_slice)

                    for v in range(vb_vert_count):
                        values = stride_func(vert_stream)
                        x, y, z = values[0], values[1], values[2]
                        verts.append((x, y, z))

                        print(f"  Vertex {v}: Pos=({x:.5f}, {y:.5f}, {z:.5f}) | Stride {stride} → {len(values)} components")
                              
                        
                    print("--------------------------------------------------")
                    print("\n ... READING INDEX DATA...")
                    print("--------------------------------------------------")
                    s.seek(index_buffer_ptr)
                    ib_vtable = rh.read_u32(s)               # 0x00
                    ib_index_count = rh.read_u32(s)          # 0x04   Indices Count
                    ib_data_offset = rh.read_data_offset(s)  # 0x08 Index Buffer Offset
                    ib_unknown1 = rh.read_u32(s)             # 0x0C   Unknown
                    ib_padding = s.read(0x30)             # 0x10 - 0x3F (padding)

                    print(f"    🔸 Full IndexBuffer Read:")
                    print(f"      VTable:       0x{ib_vtable:08X}")
                    print(f"      Index Count:  {ib_index_count}")
                    print(f"      Data Offset:  0x{ib_data_offset:08X}")
                    print(f"      Unknown 1:    0x{ib_unknown1:08X}")
                    print(f"      Padding:      {' '.join(f'{b:02X}' for b in ib_padding)}")

                    indices = []
                    index_data_offset = ib_data_offset + system_mem  # Data offset + physical size, similar to vertex data
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


def safe_read(label, func, stream):
    offset = stream.tell()
    try:
        value = func(stream)
        print(f"✅ {label} at 0x{offset:08X} = {value}")
        return value
    except Exception as e:
        print(f"❌ FAILED reading {label} at 0x{offset:08X}: {e}")
        raise

def read_rsc_header_wdd(data):
    import struct
    magic = data[:3]
    if magic != b'RSC':
        raise ValueError("Not a valid RSC header.")
    
    file_type = data[3]
    version = struct.unpack_from('<I', data, 4)[0]
    flags = struct.unpack_from('<I', data, 8)[0]

    def get_system_mem_size(flags):
        return (flags & 0x7FF) << (((flags >> 11) & 0xF) + 8)

    def get_graphics_mem_size(flags):
        return ((flags >> 15) & 0x7FF) << (((flags >> 26) & 0xF) + 8)

    system_mem = get_system_mem_size(flags)
    graphics_mem = get_graphics_mem_size(flags)
    total_mem = system_mem + graphics_mem

    print("📦 WDD RSC HEADER:")
    print(f"  FileType: 0x{file_type:02X}, Version: {version}, Flags: 0x{flags:08X}")
    print(f"  SystemMem: {system_mem}, GraphicsMem: {graphics_mem}, TotalMem: {total_mem}")
    
    return system_mem


#######################################################
def read_wdr_dictionary(self, name, data, adjusted_offset, system_mem):
    # gtaDrawable Dictionaries skip the ModelCollection selection
    # As such, for Windows Drawable Dictionaries, the WDR struct varies.
    
    try:
        with open(self.filepath, 'rb') as s:
        
            print(f"\n ...BEGIN READING FOR {name}...\n")
            s = io.BytesIO(data)                            # Slice WDRs within dictionaries into buffers
            cpu_data = data

            #######################################################

            print("--------------------------------------------------")
            print(f"\n ... READING EMBEDDED WDR HEADER FOR {name} ...")
            print("--------------------------------------------------")

            try:
                vtable = safe_read("VTable", rh.read_u32, s)
                unknown_1 = safe_read("Unknown_1", rh.read_u32, s)
                shadergroup_offset = safe_read("ShaderGroup Offset", rh.read_data_offset, s)
                unknown_2 = safe_read("Unknown_2", rh.read_u32, s)

                cx = safe_read("Center X", rh.read_f32, s)
                cy = safe_read("Center Y", rh.read_f32, s)
                cz = safe_read("Center Z", rh.read_f32, s)
                cw = safe_read("Center W", rh.read_f32, s)

                minx = safe_read("Min X", rh.read_f32, s)
                miny = safe_read("Min Y", rh.read_f32, s)
                minz = safe_read("Min Z", rh.read_f32, s)
                minw = safe_read("Min W", rh.read_f32, s)

                maxx = safe_read("Max X", rh.read_f32, s)
                maxy = safe_read("Max Y", rh.read_f32, s)
                maxz = safe_read("Max Z", rh.read_f32, s)
                maxw = safe_read("Max W", rh.read_f32, s)

                model_pointer_offset_ptr = safe_read("Model Section Offset", rh.read_data_offset, s)
                unknown_3 = safe_read("Unknown_3", rh.read_u32, s)
                unknown_4 = safe_read("Unknown_4", rh.read_u32, s)
                unknown_5 = safe_read("Unknown_5", rh.read_u32, s)

                maxvx = safe_read("MaxVec X", rh.read_f32, s)
                maxvy = safe_read("MaxVec Y", rh.read_f32, s)
                maxvz = safe_read("MaxVec Z", rh.read_f32, s)
                maxvw = safe_read("MaxVec W", rh.read_f32, s)

                obj_count = safe_read("Object Count", rh.read_u32, s)
                object_vertices = [[] for _ in range(obj_count)]
                object_indices = [[] for _ in range(obj_count)]
                current_object = 0

                print("\n🔥 EMBEDDED WDR HEADER SUMMARY:")
                print(f"  Center:      ({cx}, {cy}, {cz}, {cw})")
                print(f"  Bounds Min:  ({minx}, {miny}, {minz}, {minw})")
                print(f"  Bounds Max:  ({maxx}, {maxy}, {maxz}, {maxw})")
                print(f"  Max Vector:  ({maxvx}, {maxvy}, {maxvz}, {maxvw})")


            except Exception as e:
                print(f"❌ FATAL ERROR while reading header: {e}")
                return None

            print("--------------------------------------------------")
            print("\n ... READING MODEL SECTION...")
            print("--------------------------------------------------")
            try:
                last_offset = 0

                def debug_read(label, func):
                    nonlocal last_offset
                    print(f"🔍 {label} @ 0x{s.tell():08X}")
                    last_offset = s.tell()
                    try:
                        val = func(s)
                        print(f"✅ {label} = 0x{val:08X}" if isinstance(val, int) else f"✅ {label} = {val}")
                        return val
                    except Exception as e:
                        print(f"❌ FAILED to read {label} at 0x{s.tell():08X}: {e}")
                        print(f"🧠 Last successful reaq1q1  d was at 0x{last_offset:08X}")
                        raise
                
                fuckboi = model_pointer_offset_ptr - adjusted_offset        # Buffer slices, so we subtract the adjusted offset
                s.seek(fuckboi)
                cumhead = rh.read_data_offset(s)
                s.seek(cumhead - adjusted_offset)
                bro = rh.read_data_offset(s)
                s.seek(bro - adjusted_offset)
                bruh = rh.read_u32(s)


                geometry_collection_offset = rh.read_data_offset(s)
                number_of_geo_ptrs = rh.read_u16(s)
                number_of_geometries = rh.read_u16(s)
                vector_array_offset = rh.read_data_offset(s)
                material_array_offset = rh.read_data_offset(s)
                unk1 = rh.read_u16(s)
                unk2 = rh.read_u16(s)
                unk3 = rh.read_u16(s)
                geometry_count = rh.read_u16(s)
                model_padding = rh.read_u32(s)

                print("\n🔷 Model Block Pt 1:")
                print(f"  VTable:             0x{fuckboi:08X}")
                print(f"  VTable:             0x{cumhead:08X}")
                print(f"  VTable:             0x{bro:08X}")
                print(f"  Do we got a VTable bruh?:             0x{bruh:08X}")

                print("\n🔷 Model Block Pt 2:")
                print(f"  Geometry Ptr:       0x{geometry_collection_offset:08X}")
                print(f"  Number of Geometry Ptrs:       {number_of_geo_ptrs}")
                print(f"  Number of Geometries:          {number_of_geometries}")
                print(f"  Vector4 Array Ptr:  0x{vector_array_offset:08X}")
                print(f"  Material Array Ptr: 0x{material_array_offset:08X}")
                print(f"  Unknowns:           {unk1}, {unk2}, {unk3}")
                print(f"  Geometry Count:     {geometry_count}")
                print(f"  Padding:            0x{model_padding:08X}")


            except Exception as e:
                print(f"❌ FATAL ERROR during model section read: {e}")
                print(f"🧠 Final stream offset: 0x{s.tell():08X}")
                print(f"📏 Total data size: {len(cpu_data)} bytes")
                return None



            print("\n🔷 Model Block:")
            print(f"  Geometry Ptr:       0x{geometry_collection_offset:08X}")
            print(f"  Number of Geometry Ptrs:       {number_of_geo_ptrs}")
            print(f"  Number of Geometries:          {number_of_geometries}")
            print(f"  Vector4 Array Ptr:  0x{vector_array_offset:08X}")
            print(f"  Material Array Ptr: 0x{material_array_offset:08X}")
            print(f"  Unknowns:           {unk1}, {unk2}, {unk3}")
            print(f"  Geometry Count:     {geometry_count}")
            print(f"  Padding:            0x{model_padding:08X}")

            fucker = geometry_collection_offset - adjusted_offset   # Ahhh fug :DDDD
            s.seek(fucker)
            faggot = rh.read_data_offset(s)
            s.seek(faggot - adjusted_offset)

            print("--------------------------------------------------")
            print("\n ... READING GEOMETRY...")
            print("--------------------------------------------------")
            print("\n📏 Geometries:")
 
            geo_vtable = rh.read_u32(s)
            unk1 = rh.read_u32(s)
            unk2 = rh.read_u32(s)
            vertex_buffer_ptr = rh.read_data_offset(s)
            unk3 = rh.read_u32(s)
            unk4 = rh.read_u32(s)
            unk5 = rh.read_u32(s)
            index_buffer_ptr = rh.read_data_offset(s)
            unk6 = rh.read_u32(s)
            unk7 = rh.read_u32(s)
            unk8 = rh.read_u32(s)
            index_count = rh.read_u32(s)
            face_count = rh.read_u32(s)
            vertex_count = rh.read_u16(s)
            primitive_type = rh.read_u16(s)
            unk9 = rh.read_u32(s)
            vertex_stride = rh.read_u16(s)
                        
            vertex_data_length = vertex_count * vertex_stride
            print(f"    Vertex Data Length: {vertex_data_length} bytes")

            unk10 = rh.read_u16(s)
            unk11 = rh.read_u32(s)
            unk12 = rh.read_u32(s)
            unk13 = rh.read_u32(s)
            padding = rh.read_u32(s)

            print(f"    VTable:          0x{geo_vtable:08X}")
            print(f"    Vertex Buffer:   0x{vertex_buffer_ptr:08X}")
            print(f"    Index Buffer:    0x{index_buffer_ptr:08X}")
            print(f"    Index Count:     {index_count}")
            print(f"    Face Count:      {face_count}")
            print(f"    Vertex Count:    {vertex_count}")
            print(f"    Primitive Type:  {primitive_type}")
            print(f"    Vertex Stride:   {vertex_stride}")
            print(f"    Padding:         0x{padding:08X}")

            s.seek(vertex_buffer_ptr - adjusted_offset)

            print("--------------------------------------------------")
            print("\n ... READING VERTEX BUFFER...")
            print("--------------------------------------------------")
            vb_vtable = rh.read_u32(s)
            vb_vert_count = rh.read_u16(s)
            vb_unknown1 = rh.read_u16(s)
            vb_data_offset1 = rh.read_data_offset(s)
            vb_stride = rh.read_u32(s)
            vb_decl_offset = rh.read_data_offset(s)
            vb_unknown2 = rh.read_u32(s)
            vb_data_offset2 = rh.read_data_offset(s)
            vb_unknown3 = rh.read_u32(s)

            print(f"    🔹 Vertex Buffer:")
            print(f"      VTable:        0x{vb_vtable:08X}")
            print(f"      Vertex Count:  {vb_vert_count}")
            print(f"      Stride:        {vb_stride}")
            print(f"      Data Offset 1: 0x{vb_data_offset1:08X}")
            print(f"      Decl Offset:   0x{vb_decl_offset:08X}")
            print(f"      Data Offset 2: 0x{vb_data_offset2:08X}")

            s.seek(index_buffer_ptr - adjusted_offset)

            print("--------------------------------------------------")
            print("\n ... READING INDEX BUFFER...")
            print("--------------------------------------------------")
            ib_vtable = rh.read_u32(s)
            ib_index_count = rh.read_u32(s)
            ib_data_offset = rh.read_data_offset(s)
            ib_unknown1 = rh.read_u32(s)

            print(f"    🔸 Index Buffer:")
            print(f"      VTable:        0x{ib_vtable:08X}")
            print(f"      Index Count:   {ib_index_count}")
            print(f"      Data Offset:   0x{ib_data_offset:08X}")
            print(f"      Unknown 1:   0x{ib_unknown1:08X}")

            s.seek(vb_decl_offset - adjusted_offset)

            print("--------------------------------------------------")
            print("\n ... READING VERTEX DECLARATION...")
            print("--------------------------------------------------")
            usage_flags = rh.read_u32(s)
            stride = rh.read_u16(s)
            decoder = rh.read_u8(s)
            decl_type = rh.read_u8(s)
            unk1 = rh.read_u32(s)
            unk2 = rh.read_u32(s)

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
            s.seek(real_vtx_offset - adjusted_offset)
            data = memoryview(cpu_data)

            verts = []
                        
            stride_map = {
                28: rh.read_stride28,
                36: rh.read_stride36,
                44: rh.read_stride44,
                52: rh.read_stride52,
                60: rh.read_stride60,
                68: rh.read_stride68,
            }

            stride_func = stride_map.get(stride)
            if stride_func is None:
                raise ValueError(f"Unsupported vertex stride: {stride}")

            verts = []
            vertex_data_start = real_vtx_offset - adjusted_offset + system_mem
            vertex_buffer_slice = cpu_data[vertex_data_start : vertex_data_start + (vb_vert_count * stride)]
            vert_stream = BytesIO(vertex_buffer_slice)

            for v in range(vb_vert_count):
                values = stride_func(vert_stream)
                x, y, z = values[0], values[1], values[2]   # You can extend this unpacking later - though might do myself
                verts.append((x, y, z))

                # Optional: print debug info for each vertex, I suppose there's no way to enable/disable prints w/ a top comment
                # Maybe a debug version?
                print(f"  Vertex {v}: Pos=({x:.5f}, {y:.5f}, {z:.5f}) | Stride {stride} → {len(values)} components")
                                
            s.seek(index_buffer_ptr - adjusted_offset)

            print("--------------------------------------------------")
            print("\n ... READING INDEX DATA...")
            print("--------------------------------------------------")
            ib_vtable = rh.read_u32(s)               # 0x00
            ib_index_count = rh.read_u32(s)          # 0x04   Indices Count
            ib_data_offset = rh.read_data_offset(s)  # 0x08 Index Buffer Offset
            ib_unknown1 = rh.read_u32(s)             # 0x0C   Unknown
            ib_padding = s.read(0x30)             # 0x10 - 0x3F (padding)

            print(f"    🔸 Full IndexBuffer Read:")
            print(f"      VTable:       0x{ib_vtable:08X}")
            print(f"      Index Count:  {ib_index_count}")
            print(f"      Data Offset:  0x{ib_data_offset:08X}")
            print(f"      Unknown 1:    0x{ib_unknown1:08X}")
            print(f"      Padding:      {' '.join(f'{b:02X}' for b in ib_padding)}")

            indices = []
            index_data_offset = ib_data_offset - adjusted_offset + system_mem       # Still adding physical size
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

                base_name = os.path.splitext(name)[0]
                mesh = bpy.data.meshes.new(f"{base_name}_Mesh_{i}")
                obj = bpy.data.objects.new(f"{base_name}_Object_{i}", mesh)

                bpy.context.collection.objects.link(obj)

                tris = indices
                mesh.from_pydata(verts, [], tris)
                mesh.update()

                print(f"🚀 Created {base_name}_Object_{i} with {len(verts)} vertices and {len(tris)} triangles.")
            #######################################################                
    except Exception as e:
        print(f"❌ Failed to parse WDR: {e}")
        return {'CANCELLED'}
    #######################################################
