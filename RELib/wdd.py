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

import struct
import zlib

# Basic stuff for now.
#######################################################
def get_system_mem_size(flags):
    return (flags & 0x7FF) << (((flags >> 11) & 0xF) + 8)
#######################################################
def read_offset(f):
    return struct.unpack('<I', f.read(4))[0] & 0x0FFFFFFF
#######################################################
def read_u32(f): return struct.unpack('<I', f.read(4))[0]
#######################################################
def read_u16(f): return struct.unpack('<H', f.read(2))[0]
#######################################################
def read_wdd_header(f):
    vtable = read_u32(f)
    if vtable != 0xA4536900:
        raise ValueError("Invalid WDD VTable")
    
    blockmap = read_u32(f)
    parent_dict = read_u32(f)
    usage_count = read_u32(f)

    hash_data_offset = read_offset(f)
    hash_count = read_u16(f)
    hash_data_size = read_u16(f)

    wdr_ptr_offset = read_offset(f)
    wdr_count = read_u16(f)
    wdr_unknown = read_u16(f)

    return {
        'vtable': vtable,
        'blockmap': blockmap,
        'parent': parent_dict,
        'usage': usage_count,
        'hash_offset': hash_data_offset,
        'hash_count': hash_count,
        'hash_size': hash_data_size,
        'wdr_ptr_offset': wdr_ptr_offset,
        'wdr_count': wdr_count
    }
#######################################################
def read_wdd_hashes(f, offset, count):
    f.seek(offset)
    return [read_u32(f) for _ in range(count)]
#######################################################
def read_wdd_wdr_offsets(f, offset, count):
    f.seek(offset)
    return [read_offset(f) for _ in range(count)]
#######################################################2
def read_rsc_wdr_data(f, offset):
    f.seek(offset)
    magic = f.read(3)
    file_type = f.read(1)
    version = read_u32(f)
    flags = read_u32(f)
    system_mem = get_system_mem_size(flags)
    data = f.read(system_mem)

    try:
        decompressed = zlib.decompress(data)
    except zlib.error:
        decompressed = data  # not compressed

    return {
        'version': version,
        'flags': flags,
        'system_mem': system_mem,
        'data': decompressed
    }
