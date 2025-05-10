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
import struct

def read_u32(f): return struct.unpack('<I', f.read(4))[0]
def read_u16(f): return struct.unpack('<H', f.read(2))[0]
def read_f32(f): return struct.unpack('<f', f.read(4))[0]

def read_offset(f):
    raw = read_u32(f)
    return raw & 0x0FFFFFFF

class WBDImporter:
    def __init__(self, filepath):
        self.filepath = filepath
        self.hashes = []
        self.bounds_offsets = []

    def load(self):
        with open(self.filepath, 'rb') as f:
            vtable = read_u32(f)
            blockmap_offset = read_u32(f)
            unknown_1 = read_u32(f)
            unknown_2 = read_u32(f)

            hash_coll_offset = f.tell()
            hash_data_offset = read_offset(f)
            hash_count = read_u16(f)
            _ = read_u16(f)

            bound_coll_offset = f.tell()
            bound_ptr_offset = read_offset(f)
            bound_count = read_u16(f)
            _ = read_u16(f)

            print(f"📦 WBD File: {self.filepath}")
            print(f"  Hash Count:  {hash_count}")
            print(f"  Bounds Count: {bound_count}")
            print(f"  Hash Data Offset:  0x{hash_data_offset:X}")
            print(f"  Bounds Ptr Offset: 0x{bound_ptr_offset:X}")

            # Read model hashes
            f.seek(hash_data_offset)
            self.hashes = [read_u32(f) for _ in range(hash_count)]

            # Read pointers to bounds data
            f.seek(bound_ptr_offset)
            self.bounds_offsets = [read_offset(f) for _ in range(bound_count)]

            for i, offset in enumerate(self.bounds_offsets):
                f.seek(offset)
                self.read_bounds(f, i)

    def read_bounds(self, f, idx):
        print(f"\n📍 Bounds Entry {idx} at 0x{f.tell():08X}")
        vtable = read_u32(f)
        pivot_count = read_u16(f)
        v2 = read_u16(f)
        v3 = read_u16(f)
        v4 = read_u16(f)
        sphere_radius = read_f32(f)

        max_x = read_f32(f)
        max_y = read_f32(f)
        max_z = read_f32(f)
        _always1a = read_u32(f)

        min_x = read_f32(f)
        min_y = read_f32(f)
        min_z = read_f32(f)
        _always1b = read_u32(f)

        sphere_x = read_f32(f)
        sphere_y = read_f32(f)
        sphere_z = read_f32(f)
        _always1c = read_u32(f)

        box_x = read_f32(f)
        box_y = read_f32(f)
        box_z = read_f32(f)
        _always1d = read_u32(f)

        geom_x = read_f32(f)
        geom_y = read_f32(f)
        geom_z = read_f32(f)
        _always1e = read_u32(f)

        print(f"  VTable: 0x{vtable:X}")
        print(f"  Pivot Count: {pivot_count}, Radius: {sphere_radius:.2f}")
        print(f"  Bounding Box Min: ({min_x:.2f}, {min_y:.2f}, {min_z:.2f})")
        print(f"  Bounding Box Max: ({max_x:.2f}, {max_y:.2f}, {max_z:.2f})")
        print(f"  Sphere Pos: ({sphere_x:.2f}, {sphere_y:.2f}, {sphere_z:.2f})")
        print(f"  Model Pivot: ({geom_x:.2f}, {geom_y:.2f}, {geom_z:.2f})")
