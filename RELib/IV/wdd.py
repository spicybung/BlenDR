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

import bpy
import struct

from ..REutils import rage_iv_helpers as rh

#######################################################

def read_wdd_header(s):
    header = {}

    header['vtable']             = struct.unpack('<I', s.read(4))[0]
    header['block_map_address']  = struct.unpack('<I', s.read(4))[0]
    header['parent_dictionary']  = struct.unpack('<I', s.read(4))[0]
    header['usage_count']        = struct.unpack('<I', s.read(4))[0]

    header['hashes_offset']      = struct.unpack('<I', s.read(4))[0]
    hash_count_pair              = struct.unpack('<HH', s.read(4))
    header['hashes_count']       = hash_count_pair[0]
    header['hashes_stride']      = hash_count_pair[1]

    header['wdrs_offset']        = struct.unpack('<I', s.read(4))[0]
    wdr_count_pair               = struct.unpack('<HH', s.read(4))
    header['wdrs_count']         = wdr_count_pair[0]
    header['wdrs_flags']         = wdr_count_pair[1]

    header['unknown']            = struct.unpack('<I', s.read(4))[0]

    padding = s.read(12)
    header['padding'] = padding
    header['valid_padding'] = all(b == 0xCD for b in padding)

    print("== WDD Header ==")
    print(f"VTable:            0x{header['vtable']:08X}")
    print(f"BlockMapAddress:   0x{header['block_map_address']:08X}")
    print(f"ParentDictionary:  0x{header['parent_dictionary']:08X}")
    print(f"UsageCount:        {header['usage_count']}")
    print(f"Hashes Offset:     0x{header['hashes_offset']:08X}")
    print(f"Hashes Count:      {header['hashes_count']} (Stride: {header['hashes_stride']})")
    print(f"WDRs Offset:       0x{header['wdrs_offset']:08X}")
    print(f"WDRs Count:        {header['wdrs_count']} (Flags: {header['wdrs_flags']})")
    print(f"Unknown:           0x{header['unknown']:08X}")
    print(f"Padding:           {padding.hex().upper()}")
    print(f"Padding OK:        {header['valid_padding']}")

    return header

def read_wdd_hashes(s, offset, count, stride):
    s.seek(offset)
    return [struct.unpack('<II', s.read(8)) for _ in range(count)]  # hash + rel_ptr

def read_wdd_wdr_offsets(s, offset, count):
    s.seek(offset)
    return [struct.unpack('<I', s.read(4))[0] for _ in range(count)]
