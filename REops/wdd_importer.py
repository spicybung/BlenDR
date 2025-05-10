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
import zlib 
import struct

import os
import io
from ..RELib.wdd import (
    read_wdd_header,
    read_wdd_hashes,
    read_wdd_wdr_offsets,
    read_rsc_wdr_data
)
from ..RELib.wdr import IMPORT_OT_wdr_reader


class WDDImporter:
    def __init__(self, filepath):
        self.filepath = filepath
        self.hashes = []
        self.wdr_offsets = []

    def load(self):
        with open(self.filepath, 'rb') as f:
            header = read_wdd_header(f)
            print(f"📦 WDD File: {self.filepath}")
            print(f"  Hashes: {header['hash_count']}, Pointers: {header['wdr_count']}")
            print(f"  Hash Offset: 0x{header['hash_offset']:X}")
            print(f"  Pointer Offset: 0x{header['wdr_ptr_offset']:X}")

            self.hashes = read_wdd_hashes(f, header['hash_offset'], header['hash_count'])
            self.wdr_offsets = read_wdd_wdr_offsets(f, header['wdr_ptr_offset'], header['wdr_count'])

            for idx, offset in enumerate(self.wdr_offsets):
                print(f"\n🧩 WDR {idx} at 0x{offset:X}")
                wdr_info = read_rsc_wdr_data(f, offset)

                print(f"  RSC Version: {wdr_info['version']}, System Mem: {wdr_info['system_mem']} bytes")
                print(f"  Decompressed Size: {len(wdr_info['data'])} bytes")

                stream = io.BytesIO(wdr_info['data'])
                wdr_reader = IMPORT_OT_wdr_reader()
                wdr_reader.filepath = f"{self.filepath}_wdr_{idx}"
                wdr_reader.execute_from_memory(stream, wdr_info['system_mem'])
