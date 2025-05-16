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

import struct

def read_u8(s): 
    return struct.unpack('<B', s.read(1))[0]
#######################################################
def read_u16(s): 
    return struct.unpack('<H', s.read(2))[0]
#######################################################
def read_u32(s): 
    return struct.unpack('<I', s.read(4))[0]
#######################################################
def read_f32(s): 
    return struct.unpack('<f', s.read(4))[0]
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
#######################################################
def ubyte(f): 
    return struct.unpack('<B', f.read(1))
#######################################################
def ushort(f): 
    return struct.unpack('<H', f.read(2))
#######################################################
def ufloat(f): 
    return struct.unpack('<f', f.read(4))
#######################################################     # Thanks to Utopiadeferred for stride functions
def read_stride28(f):
    x, y, z = ufloat(f)[0], ufloat(f)[0], ufloat(f)[0]
    r, g, b, a = ubyte(f)[0], ubyte(f)[0], ubyte(f)[0], ubyte(f)[0]
    r2, g2, b2, a2 = ubyte(f)[0], ubyte(f)[0], ubyte(f)[0], ubyte(f)[0]
    u, v = ufloat(f)[0], ufloat(f)[0]
    return (x, y, z, r, g, b, a, r2, g2, b2, a2, u, v)
#######################################################
def read_stride36(f):
    x, y, z = ufloat(f)[0], ufloat(f)[0], ufloat(f)[0]
    nx, ny, nz = ufloat(f)[0], ufloat(f)[0], ufloat(f)[0]
    r, g, b, a = ubyte(f)[0], ubyte(f)[0], ubyte(f)[0], ubyte(f)[0]
    u, v = ufloat(f)[0], ufloat(f)[0]
    return (x, y, z, nx, ny, nz, r, g, b, a, u, v)
#######################################################
def read_stride44(f):
    x, y, z = ufloat(f)[0], ufloat(f)[0], ufloat(f)[0]
    bw1, bw2, bw3, bw4 = ubyte(f)[0], ubyte(f)[0], ubyte(f)[0], ubyte(f)[0]
    bi1, bi2, bi3, bi4 = ubyte(f)[0], ubyte(f)[0], ubyte(f)[0], ubyte(f)[0]
    nx, ny, nz = ufloat(f)[0], ufloat(f)[0], ufloat(f)[0]
    r, g, b, a = ubyte(f)[0], ubyte(f)[0], ubyte(f)[0], ubyte(f)[0]
    u, v = ufloat(f)[0], ufloat(f)[0]
    return (x, y, z, bw1, bw2, bw3, bw4, bi1, bi2, bi3, bi4, nx, ny, nz, r, g, b, a, u, v)
#######################################################
def read_stride52(f):
    x, y, z = ufloat(f)[0], ufloat(f)[0], ufloat(f)[0]
    nx, ny, nz = ufloat(f)[0], ufloat(f)[0], ufloat(f)[0]
    r, g, b, a = ubyte(f)[0], ubyte(f)[0], ubyte(f)[0], ubyte(f)[0]
    u, v = ufloat(f)[0], ufloat(f)[0]
    tx, ty, tz, tw = ufloat(f)[0], ufloat(f)[0], ufloat(f)[0], ufloat(f)[0]
    return (x, y, z, nx, ny, nz, r, g, b, a, u, v, tx, ty, tz, tw)
#######################################################
def read_stride60(f):
    x, y, z = ufloat(f)[0], ufloat(f)[0], ufloat(f)[0]
    bw1, bw2, bw3, bw4 = ubyte(f)[0], ubyte(f)[0], ubyte(f)[0], ubyte(f)[0]
    bi1, bi2, bi3, bi4 = ubyte(f)[0], ubyte(f)[0], ubyte(f)[0], ubyte(f)[0]
    nx, ny, nz = ufloat(f)[0], ufloat(f)[0], ufloat(f)[0]
    r, g, b, a = ubyte(f)[0], ubyte(f)[0], ubyte(f)[0], ubyte(f)[0]
    u, v = ufloat(f)[0], ufloat(f)[0]
    tx, ty, tz, tw = ufloat(f)[0], ufloat(f)[0], ufloat(f)[0], ufloat(f)[0]
    return (x, y, z, bw1, bw2, bw3, bw4, bi1, bi2, bi3, bi4, nx, ny, nz, r, g, b, a, u, v, tx, ty, tz, tw)
#######################################################
def read_stride68(f):
    x, y, z = ufloat(f)[0], ufloat(f)[0], ufloat(f)[0]
    bw1, bw2, bw3, bw4 = ubyte(f)[0], ubyte(f)[0], ubyte(f)[0], ubyte(f)[0]
    bi1, bi2, bi3, bi4 = ubyte(f)[0], ubyte(f)[0], ubyte(f)[0], ubyte(f)[0]
    nx, ny, nz = ufloat(f)[0], ufloat(f)[0], ufloat(f)[0]
    r, g, b, a = ubyte(f)[0], ubyte(f)[0], ubyte(f)[0], ubyte(f)[0]
    u, v = ufloat(f)[0], ufloat(f)[0]
    u2, v2 = ufloat(f)[0], ufloat(f)[0]
    tx, ty, tz, tw = ufloat(f)[0], ufloat(f)[0], ufloat(f)[0], ufloat(f)[0]
    return (x, y, z, bw1, bw2, bw3, bw4, bi1, bi2, bi3, bi4, nx, ny, nz, r, g, b, a, u, v, u2, v2, tx, ty, tz, tw)
#######################################################
def read_indices(f):
    vertexA, vertexB, vertexC = ushort(f)[0], ushort(f)[0], ushort(f)[0]
    return (vertexA, vertexB, vertexC)
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

def jump_and_read_u32_at(stream, offset):
    stream.seek(offset)
    return read_u32_from_stream(stream)

#######################################################
def jump_and_read_u32(self, stream, offset):

    stream.seek(offset + 12)
    return self.read_u32_from_stream(stream)
#######################################################