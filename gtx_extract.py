#!/usr/bin/env python

# GTX Extractor
# Version v2.0
# Copyright © 2014 Treeki, 2015-2016 AboodXD

# This file is part of GTX Extractor.

# GTX Extractor is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# GTX Extractor is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""gtx_extract.py: Decode GFD (GTX/GSH) images."""

import os, struct, sys, time, subprocess

from PyQt5 import QtCore, QtGui
Qt = QtCore.Qt

__author__ = "AboodXD"
__copyright__ = "Copyright 2014 Treeki, 2015-2016 AboodXD"
__credits__ = ["AboodXD", "libtxc_dxtn", "Treeki",
                    "Reggie Next! team", "Exzap"]

formats = {0x00000000: 'GX2_SURFACE_FORMAT_INVALID',
           0x00000823: 'GX2_SURFACE_FORMAT_TC_R32_G32_B32_A32_FLOAT',
           0x0000001f: 'GX2_SURFACE_FORMAT_TC_R16_G16_B16_A16_UNORM',
           0x00000820: 'GX2_SURFACE_FORMAT_TC_R16_G16_B16_A16_FLOAT',
           0x0000001a: 'GX2_SURFACE_FORMAT_TCS_R8_G8_B8_A8_UNORM',
           0x0000041a: 'GX2_SURFACE_FORMAT_TCS_R8_G8_B8_A8_SRGB',
           0x00000019: 'GX2_SURFACE_FORMAT_TCS_R10_G10_B10_A2_UNORM',
           0x00000008: 'GX2_SURFACE_FORMAT_TCS_R5_G6_B5_UNORM',
           0x0000000a: 'GX2_SURFACE_FORMAT_TC_R5_G5_B5_A1_UNORM',
           0x0000000b: 'GX2_SURFACE_FORMAT_TC_R4_G4_B4_A4_UNORM',
           0x00000001: 'GX2_SURFACE_FORMAT_TC_R8_UNORM',
           0x00000031: 'GX2_SURFACE_FORMAT_T_BC1_UNORM',
           0x00000431: 'GX2_SURFACE_FORMAT_T_BC1_SRGB',
           0x00000032: 'GX2_SURFACE_FORMAT_T_BC2_UNORM',
           0x00000432: 'GX2_SURFACE_FORMAT_T_BC2_SRGB',
           0x00000033: 'GX2_SURFACE_FORMAT_T_BC3_UNORM',
           0x00000433: 'GX2_SURFACE_FORMAT_T_BC3_SRGB'
           }

false = 0
true = 1

m_banks = 4
m_banksBitcount = 2
m_pipes = 2
m_pipesBitcount = 1
m_pipeInterleaveBytes = 256
m_pipeInterleaveBytesBitcount = 8
m_rowSize = 2048
m_swapSize = 256
m_splitSize = 2048

m_chipFamily = 2

# ----------\/-Start of libtxc_dxtn section-\/---------- #
def EXP5TO8R(packedcol):
    return int((((packedcol) >> 8) & 0xf8) | (((packedcol) >> 13) & 0x07))

def EXP6TO8G(packedcol):
    return int((((packedcol) >> 3) & 0xfc) | (((packedcol) >>  9) & 0x03))

def EXP5TO8B(packedcol):
    return int((((packedcol) << 3) & 0xf8) | (((packedcol) >>  2) & 0x07))

def EXP4TO8(col):
    return int((col) | ((col) << 4))

# inefficient. To be efficient, it would be necessary to decode 16 pixels at once

def dxt135_decode_imageblock(pixdata, img_block_src, i, j, dxt_type):
    color0 = pixdata[img_block_src] | (pixdata[img_block_src + 1] << 8)
    color1 = pixdata[img_block_src + 2] | (pixdata[img_block_src + 3] << 8)
    bits = pixdata[img_block_src + 4] | (pixdata[img_block_src + 5] << 8) | (pixdata[img_block_src + 6] << 16) | (pixdata[img_block_src + 7] << 24)
    # What about big/little endian?
    bit_pos = 2 * (j * 4 + i)
    code = (bits >> bit_pos) & 3

    ACOMP = 255
    if code == 0:
        RCOMP = EXP5TO8R(color0)
        GCOMP = EXP6TO8G(color0)
        BCOMP = EXP5TO8B(color0)
    elif code == 1:
        RCOMP = EXP5TO8R(color1)
        GCOMP = EXP6TO8G(color1)
        BCOMP = EXP5TO8B(color1)
    elif code == 2:
        if (dxt_type > 1) or (color0 > color1):
            RCOMP = ((EXP5TO8R(color0) * 2 + EXP5TO8R(color1)) // 3)
            GCOMP = ((EXP6TO8G(color0) * 2 + EXP6TO8G(color1)) // 3)
            BCOMP = ((EXP5TO8B(color0) * 2 + EXP5TO8B(color1)) // 3)
        else:
            RCOMP = ((EXP5TO8R(color0) + EXP5TO8R(color1)) // 2)
            GCOMP = ((EXP6TO8G(color0) + EXP6TO8G(color1)) // 2)
            BCOMP = ((EXP5TO8B(color0) + EXP5TO8B(color1)) // 2)
    elif code == 3:
        if (dxt_type > 1) or (color0 > color1):
            RCOMP = ((EXP5TO8R(color0) + EXP5TO8R(color1) * 2) // 3)
            GCOMP = ((EXP6TO8G(color0) + EXP6TO8G(color1) * 2) // 3)
            BCOMP = ((EXP5TO8B(color0) + EXP5TO8B(color1) * 2) // 3)
        else:
            RCOMP = 0
            GCOMP = 0
            BCOMP = 0
            if dxt_type == 1: ACOMP = 0
    else:
        # CANNOT happen (I hope)
        pass

    return ACOMP, RCOMP, GCOMP, BCOMP

def fetch_2d_texel_rgb_dxt1(srcRowStride, pixdata, i, j):

    """
    Extract the (i,j) pixel from pixdata and return it
    in RCOMP, GCOMP, BCOMP, ACOMP.
    """

    blksrc = ((srcRowStride + 3) // 4 * (j // 4) + (i // 4)) * 8
    ACOMP, RCOMP, GCOMP, BCOMP = dxt135_decode_imageblock(pixdata, blksrc, i & 3, j & 3, 0)

    return bytes([RCOMP, GCOMP, BCOMP, ACOMP])

def fetch_2d_texel_rgba_dxt1(srcRowStride, pixdata, i, j):

    """
    Extract the (i,j) pixel from pixdata and return it
    in RCOMP, GCOMP, BCOMP, ACOMP.
    """

    blksrc = ((srcRowStride + 3) // 4 * (j // 4) + (i // 4)) * 8
    ACOMP, RCOMP, GCOMP, BCOMP = dxt135_decode_imageblock(pixdata, blksrc, i & 3, j & 3, 1)

    return bytes([RCOMP, GCOMP, BCOMP, ACOMP])

def fetch_2d_texel_rgba_dxt3(srcRowStride, pixdata, i, j):

    """
    Extract the (i,j) pixel from pixdata and return it
    in RCOMP, GCOMP, BCOMP, ACOMP.
    """

    blksrc = ((srcRowStride + 3) // 4 * (j // 4) + (i // 4)) * 16
    anibble = (pixdata[blksrc + ((j & 3) * 4 + (i & 3)) // 2] >> (4 * (i & 1))) & 0x0f
    ACOMP, RCOMP, GCOMP, BCOMP = dxt135_decode_imageblock(pixdata, blksrc + 8, i & 3, j & 3, 2)
    ACOMP = EXP4TO8(anibble)

    return bytes([RCOMP, GCOMP, BCOMP, ACOMP])

def fetch_2d_texel_rgba_dxt5(srcRowStride, pixdata, i, j):

    """
    Extract the (i,j) pixel from pixdata and return it
    in RCOMP, GCOMP, BCOMP, ACOMP.
    """

    blksrc = ((srcRowStride + 3) // 4 * (j // 4) + (i // 4)) * 16
    alpha0 = pixdata[blksrc]
    alpha1 = pixdata[blksrc + 1]
    # TODO test this!
    bit_pos = ((j & 3) * 4 + (i & 3)) * 3
    acodelow = pixdata[blksrc + 2 + bit_pos // 8]
    acodehigh = pixdata[blksrc + 3 + bit_pos // 8]
    code = (acodelow >> (bit_pos & 0x07) |
        (acodehigh << (8 - (bit_pos & 0x07)))) & 0x07
    ACOMP, RCOMP, GCOMP, BCOMP = dxt135_decode_imageblock(pixdata, blksrc + 8, i & 3, j & 3, 2)

    if code == 0:
        ACOMP = alpha0
    elif code == 1:
        ACOMP = alpha1
    elif alpha0 > alpha1:
        ACOMP = (alpha0 * (8 - code) + (alpha1 * (code - 1))) // 7
    elif code < 6:
        ACOMP = (alpha0 * (6 - code) + (alpha1 * (code - 1))) // 5
    elif code == 6:
        ACOMP = 0
    else:
        ACOMP = 255

    return bytes([RCOMP, GCOMP, BCOMP, ACOMP])

def fetch_2d_texel_rgba_dxt(data, width, height, format_):

    """
    Does the decompression for DXT compressed images.
    """

    output = bytearray()

    for y in range(height):
        for x in range(width):
            if (format_ == 0x31 or format_ == 0x431):
                try:
                    outValue = fetch_2d_texel_rgba_dxt1(width, data, x, y)
                    pos__ = (y * width + x) * 4
                    output[pos__:pos__ + 4] = outValue
                except:
                    outValue = fetch_2d_texel_rgb_dxt1(width, data, x, y)
                    pos__ = (y * width + x) * 4
                    output[pos__:pos__ + 4] = outValue
            elif (format_ == 0x32 or format_ == 0x432):
                outValue = fetch_2d_texel_rgba_dxt3(width, data, x, y)
                pos__ = (y * width + x) * 4
                output[pos__:pos__ + 4] = outValue
            elif (format_ == 0x33 or format_ == 0x433):
                outValue = fetch_2d_texel_rgba_dxt5(width, data, x, y)
                pos__ = (y * width + x) * 4
                output[pos__:pos__ + 4] = outValue

    return output
    
# ----------\/-Start of GFD Extracting section-\/------------- #
class GFDData():
    width, height = 0, 0
    format = 0
    dataSize = 0
    data = b''

class GFDHeader(struct.Struct):
    def __init__(self):
        super().__init__('>4s7I') # Totally stolen, thanks Reggie Next team!

    def data(self, data, pos):
        (self.magic,
        self.size_,
        self.majorVersion,
        self.minorVersion,
        self.gpuVersion,
        self.alignMode,
        self.reserved1,
        self.reserved2) = self.unpack_from(data, pos)

class GFDBlockHeader(struct.Struct):
    def __init__(self):
        super().__init__('>4s7I') # Totally stolen, thanks Reggie Next team!

    def data(self, data, pos):
        (self.magic,
        self.size_,
        self.majorVersion,
        self.minorVersion,
        self.type_,
        self.dataSize,
        self.id,
        self.typeIdx) = self.unpack_from(data, pos)

class GFDSurface(struct.Struct):
    def __init__(self):
        super().__init__('>39I') # Totally stolen, thanks Reggie Next team!

    def data(self, data, pos):
        (self.dim,
        self.width,
        self.height,
        self.depth,
        self.numMips,
        self.format_,
        self.aa,
        self.use,
        self.imageSize,
        self.imagePtr,
        self.mipSize,
        self.mipPtr,
        self.tileMode,
        self.swizzle,
        self.alignment,
        self.pitch,
        self.mipOffset,
        self._44,
        self._48,
        self._4C,
        self._50,
        self._54,
        self._58,
        self._5C,
        self._60,
        self._64,
        self._68,
        self._6C,
        self._70,
        self._74,
        self._78,
        self._7C,
        self._80,
        self._84,
        self._88,
        self._8C,
        self._90,
        self._94,
        self._98) = self.unpack_from(data, pos)

def readGFD(f):
    gfd = GFDData()
    pos = 0

    header = GFDHeader()

    # This is kinda bad. Don't really care right now >.>
    gfd.width = 0
    gfd.height = 0
    gfd.data = b''

    header.data(f, pos)
    
    if header.magic != b'Gfx2':
        raise ValueError("Invalid file header!")

    pos += header.size

    while pos < len(f):
        block = GFDBlockHeader()
        block.data(f, pos)

        if block.magic != b'BLK{':
            raise ValueError("Invalid block header!")

        pos += block.size

        if block.type_ == 0x0B:
            surface = GFDSurface()
            surface.data(f, pos)

            pos += surface.size

            gfd.dim = surface.dim
            gfd.width = surface.width
            gfd.height = surface.height
            gfd.depth = surface.depth
            gfd.numMips = surface.numMips
            gfd.format = surface.format_
            gfd.aa = surface.aa
            gfd.use = surface.use
            gfd.imageSize = surface.imageSize
            gfd.imagePtr = surface.imagePtr
            gfd.mipSize = surface.mipSize
            gfd.mipPtr = surface.mipPtr
            gfd.tileMode = surface.tileMode
            gfd.swizzle = surface.swizzle
            gfd.alignment = surface.alignment
            gfd.pitch = surface.pitch
            #gfd.mipOffset = f[0x80:0x80 + 0x13]

        elif block.type_ == 0x0C and len(gfd.data) == 0:
            gfd.dataSize = block.dataSize
            gfd.data = f[pos:pos + block.dataSize]
            pos += block.dataSize

        else:
            pos += block.dataSize

    return gfd

def swapRB(bgra):
    return bytes((bgra[2], bgra[1], bgra[0], bgra[3]))

def writePNG(gfd):
    if gfd.format in formats:
        if gfd.format == 0x00:
            raise ValueError("Invalid texture format!")

        else:
            if (gfd.format != 0x31 and gfd.format != 0x431 and gfd.format != 0x32 and gfd.format != 0x432 and gfd.format != 0x33 and gfd.format != 0x433):
                result = swizzle(gfd.width, gfd.height, gfd.depth, gfd.format, gfd.tileMode, gfd.swizzle, gfd.pitch, gfd.data)

                img = QtGui.QImage(result, gfd.width, gfd.height, QtGui.QImage.Format_RGBA8888)

            else:
                result = swizzle_BC(gfd.width, gfd.height, gfd.depth, gfd.format, gfd.tileMode, gfd.swizzle, gfd.pitch, gfd.data)
                output = fetch_2d_texel_rgba_dxt(result, gfd.width, gfd.height, gfd.format)

                img = QtGui.QImage(output, gfd.width, gfd.height, QtGui.QImage.Format_RGBA8888)

    else:
        print("")
        print("Unsupported texture format: " + hex(gfd.format))
        print("Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    yield img.copy(0, 0, gfd.width, gfd.height)

# ----------\/-Start of the swizzling section-\/---------- #
def swizzle(width, height, depth, format_, tileMode, swizzle, pitch, data):
    result = bytearray()

    for y in range(height):
        for x in range(width):
            bitPos = 0
            bpp = surfaceGetBitsPerPixel(format_)
            pipeSwizzle = (swizzle >> 8) & 1
            bankSwizzle = (swizzle >> 9) & 3

            if (tileMode == 0 or tileMode == 1):
                pos = AddrLib_computeSurfaceAddrFromCoordLinear(x, y, 0, 0, bpp, pitch, height, depth, bitPos)
            elif (tileMode == 2 or tileMode == 3):
                pos = AddrLib_computeSurfaceAddrFromCoordMicroTiled(x, y, 0, bpp, pitch, height, tileMode, false, 0, 0, bitPos)
            else:
                pos = AddrLib_computeSurfaceAddrFromCoordMacroTiled(x, y, 0, 0, bpp, pitch, height, 1, tileMode, false, 0, 0, pipeSwizzle, bankSwizzle, bitPos)

            pos_ = (y * width + x) * 4

            result[pos_:pos_ + 4] = data[pos:pos + 4]

    return result

def swizzle_BC(width, height, depth, format_, tileMode, swizzle, pitch, data):
    result = bytearray()

    width = width // 4
    height = height // 4

    for y in range(height):
        for x in range(width):
            bitPos = 0
            bpp = surfaceGetBitsPerPixel(format_)
            pipeSwizzle = (swizzle >> 8) & 1
            bankSwizzle = (swizzle >> 9) & 3

            if (tileMode == 0 or tileMode == 1):
                pos = AddrLib_computeSurfaceAddrFromCoordLinear(x, y, 0, 0, bpp, pitch, height, depth, bitPos)
            elif (tileMode == 2 or tileMode == 3):
                pos = AddrLib_computeSurfaceAddrFromCoordMicroTiled(x, y, 0, bpp, pitch, height, tileMode, false, 0, 0, bitPos)
            else:
                pos = AddrLib_computeSurfaceAddrFromCoordMacroTiled(x, y, 0, 0, bpp, pitch, height, 1, tileMode, false, 0, 0, pipeSwizzle, bankSwizzle, bitPos)

            if (format_ == 0x31 or format_ == 0x431):
                pos_ = (y * width + x) * 8

                result[pos_:pos_ + 8] = data[pos:pos + 8]
            else:
                pos_ = (y * width + x) * 16

                result[pos_:pos_ + 16] = data[pos:pos + 16]

    return result

# I'd like to give a huge thanks to Exzap for this,
# Thanks Exzap!

formatHwInfo = b"\x00\x00\x00\x01\x08\x03\x00\x01\x08\x01\x00\x01\x00\x00\x00\x01" \
    b"\x00\x00\x00\x01\x10\x07\x00\x00\x10\x03\x00\x01\x10\x03\x00\x01" \
    b"\x10\x0B\x00\x01\x10\x01\x00\x01\x10\x03\x00\x01\x10\x03\x00\x01" \
    b"\x10\x03\x00\x01\x20\x03\x00\x00\x20\x07\x00\x00\x20\x03\x00\x00" \
    b"\x20\x03\x00\x01\x20\x05\x00\x00\x00\x00\x00\x00\x20\x03\x00\x00" \
    b"\x00\x00\x00\x00\x00\x00\x00\x01\x20\x03\x00\x01\x00\x00\x00\x01" \
    b"\x00\x00\x00\x01\x20\x0B\x00\x01\x20\x0B\x00\x01\x20\x0B\x00\x01" \
    b"\x40\x05\x00\x00\x40\x03\x00\x00\x40\x03\x00\x00\x40\x03\x00\x00" \
    b"\x40\x03\x00\x01\x00\x00\x00\x00\x80\x03\x00\x00\x80\x03\x00\x00" \
    b"\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x10\x01\x00\x00" \
    b"\x10\x01\x00\x00\x20\x01\x00\x00\x20\x01\x00\x00\x20\x01\x00\x00" \
    b"\x00\x01\x00\x01\x00\x01\x00\x00\x00\x01\x00\x00\x60\x01\x00\x00" \
    b"\x60\x01\x00\x00\x40\x01\x00\x01\x80\x01\x00\x01\x80\x01\x00\x01" \
    b"\x40\x01\x00\x01\x80\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00" \
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" \
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"

def surfaceGetBitsPerPixel(surfaceFormat):
    hwFormat = surfaceFormat & 0x3F
    bpp = formatHwInfo[hwFormat * 4 + 0]
    return bpp

def computeSurfaceThickness(tileMode):
    if (tileMode == 3 or tileMode == 7 or tileMode == 11 or tileMode == 13 or tileMode == 15):
        thickness = 4
    elif (tileMode == 16 or tileMode == 17):
        thickness = 8
    else:
        thickness = 1
    return thickness

def computePixelIndexWithinMicroTile(x, y, z, bpp, tileMode, microTileType):
    pixelBit6 = 0
    pixelBit7 = 0
    pixelBit8 = 0
    thickness = computeSurfaceThickness(tileMode)

    if microTileType == 3:
        pixelBit0 = x & 1
        pixelBit1 = y & 1
        pixelBit2 = z & 1
        pixelBit3 = (x & 2) >> 1
        pixelBit4 = (y & 2) >> 1
        pixelBit5 = (z & 2) >> 1
        pixelBit6 = (x & 4) >> 2
        pixelBit7 = (y & 4) >> 2
    else:
        if microTileType != 0:
            pixelBit0 = x & 1
            pixelBit1 = y & 1
            pixelBit2 = (x & 2) >> 1
            pixelBit3 = (y & 2) >> 1
            pixelBit4 = (x & 4) >> 2
            pixelBit5 = (y & 4) >> 2
        else:
            if bpp == 0x08:
                pixelBit0 = x & 1
                pixelBit1 = (x & 2) >> 1
                pixelBit2 = (x & 4) >> 2
                pixelBit3 = (y & 2) >> 1
                pixelBit4 = y & 1
                pixelBit5 = (y & 4) >> 2
            elif bpp == 0x10:
                pixelBit0 = x & 1
                pixelBit1 = (x & 2) >> 1
                pixelBit2 = (x & 4) >> 2
                pixelBit3 = y & 1
                pixelBit4 = (y & 2) >> 1
                pixelBit5 = (y & 4) >> 2
            elif (bpp == 0x20 or bpp == 0x60):
                pixelBit0 = x & 1
                pixelBit1 = (x & 2) >> 1
                pixelBit2 = y & 1
                pixelBit3 = (x & 4) >> 2
                pixelBit4 = (y & 2) >> 1
                pixelBit5 = (y & 4) >> 2
            elif bpp == 0x40:
                pixelBit0 = x & 1
                pixelBit1 = y & 1
                pixelBit2 = (x & 2) >> 1
                pixelBit3 = (x & 4) >> 2
                pixelBit4 = (y & 2) >> 1
                pixelBit5 = (y & 4) >> 2
            elif bpp == 0x80:
                pixelBit0 = y & 1
                pixelBit1 = x & 1
                pixelBit2 = (x & 2) >> 1
                pixelBit3 = (x & 4) >> 2
                pixelBit4 = (y & 2) >> 1
                pixelBit5 = (y & 4) >> 2
            else:
                pixelBit0 = x & 1
                pixelBit1 = (x & 2) >> 1
                pixelBit2 = y & 1
                pixelBit3 = (x & 4) >> 2
                pixelBit4 = (y & 2) >> 1
                pixelBit5 = (y & 4) >> 2
        if thickness > 1:
            pixelBit6 = z & 1
            pixelBit7 = (z & 2) >> 1
    if thickness == 8:
        pixelBit8 = (z & 4) >> 2
    return (pixelBit8 << 8) | (pixelBit7 << 7) | (pixelBit6 << 6) | 32 * pixelBit5 | 16 * pixelBit4 | 8 * pixelBit3 | 4 * pixelBit2 | pixelBit0 | 2 * pixelBit1

def computePipeFromCoordWoRotation(x, y):
    # hardcoded to assume 2 pipes
    pipe = ((y >> 3) ^ (x >> 3)) & 1
    return pipe

def computeBankFromCoordWoRotation(x, y):
    numPipes = m_pipes
    numBanks = m_banks
    bankOpt = 0
    if numBanks == 4:
        bankBit0 = ((y // (16 * numPipes)) ^ (x >> 3)) & 1
        if (bankOpt == 1 and numPipes == 8):
            bankBit0 ^= x // 0x20 & 1
        bank = bankBit0 | 2 * (((y // (8 * numPipes)) ^ (x >> 4)) & 1)
    elif numBanks == 8:
        bankBit0a = ((y // (32 * numPipes)) ^ (x >> 3)) & 1
        if (bankOpt == 1 and numPipes == 8):
            bankBit0a ^= x // (8 * numBanks) & 1
        bank = bankBit0a | 2 * (((y // (32 * numPipes)) ^ (y // (16 * numPipes) ^ (x >> 4))) & 1) | 4 * (((y // (8 * numPipes)) ^ (x >> 5)) & 1)
    else:
        bank = 0

    return bank

def computeSurfaceRotationFromTileMode(tileMode):
    pipes = m_pipes
    if (tileMode == 4 or tileMode == 5 or tileMode == 6 or tileMode == 7 or tileMode == 8 or tileMode == 9 or tileMode == 10 or tileMode == 11):
        result = pipes * ((m_banks >> 1) - 1)
    elif (tileMode == 12 or tileMode == 13 or tileMode == 14 or tileMode == 15):
        if (pipes > 4 or pipes == 4):
            result = (pipes >> 1) - 1
        else:
            result = 1
    else:
        result = 0
    return result

def isThickMacroTiled(tileMode):
    thickMacroTiled = 0
    if (tileMode == 7 or tileMode == 11 or tileMode == 13 or tileMode == 15):
        thickMacroTiled = 1
    else:
        thickMacroTiled = thickMacroTiled
    return thickMacroTiled

def isBankSwappedTileMode(tileMode):
    bankSwapped = 0
    if (tileMode == 8 or tileMode == 9 or tileMode == 10 or tileMode == 11 or tileMode == 14 or tileMode == 15):
        bankSwapped = 1
    else:
        bankSwapped = bankSwapped
    return bankSwapped

def computeMacroTileAspectRatio(tileMode):
    ratio = 1
    if (tileMode == 8 or tileMode == 12 or tileMode == 14):
        ratio = 1
    elif (tileMode == 5 or tileMode == 9):
        ratio = 2
    elif (tileMode == 6 or tileMode == 10):
        ratio = 4
    else:
        ratio = ratio
    return ratio

def computeSurfaceBankSwappedWidth(tileMode, bpp, numSamples, pitch, pSlicesPerTile):
    bankSwapWidth = 0
    numBanks = m_banks
    numPipes = m_pipes
    swapSize = m_swapSize
    rowSize = m_rowSize
    splitSize = m_splitSize
    groupSize = m_pipeInterleaveBytes
    slicesPerTile = 1
    bytesPerSample = 8 * bpp & 0x1FFFFFFF
    samplesPerTile = splitSize // bytesPerSample
    if (splitSize // bytesPerSample) != 0:
        slicesPerTile = numSamples // samplesPerTile
        if not ((numSamples // samplesPerTile) != 0):
            slicesPerTile = 1
    if pSlicesPerTile != 0:
        pSlicesPerTile = slicesPerTile
    if isThickMacroTiled(tileMode) == 1:
        numSamples = 4
    bytesPerTileSlice = numSamples * bytesPerSample // slicesPerTile
    if isBankSwappedTileMode(tileMode) != 0:
        factor = computeMacroTileAspectRatio(tileMode)
        swapTiles = (swapSize >> 1) // bpp
        if swapTiles != 0:
            v9 = swapTiles
        else:
            v9 = 1
        swapWidth = v9 * 8 * numBanks
        heightBytes = numSamples * factor * numPipes * bpp // slicesPerTile
        swapMax = numPipes * numBanks * rowSize // heightBytes
        swapMin = groupSize * 8 * numBanks // bytesPerTileSlice
        if (swapMax > swapWidth or swapMax == swapWidth):
            if (swapMin < swapWidth or swapMin == swapWidth):
                v7 = swapWidth
            else:
                v7 = swapMin
            v8 = v7
        else:
            v8 = swapMax
        bankSwapWidth = v8
        while bankSwapWidth >= (2 * pitch): # Let's wish this works :P
            bankSwapWidth >>= 1
    return bankSwapWidth

def bankSwapOrder(data):
    return bytes((data[0], data[1], data[3], data[2]))

def AddrLib_getTileType(isDepth):
    return (1 if isDepth != 0 else 0)

def AddrLib_computePixelIndexWithinMicroTile(x, y, z, bpp, tileMode, microTileType):
    pixelBit6 = 0
    pixelBit7 = 0
    pixelBit8 = 0
    thickness = computeSurfaceThickness(tileMode)
    if microTileType == 3:
        pixelBit0 = x & 1
        pixelBit1 = y & 1
        pixelBit2 = z & 1
        pixelBit3 = (x & 2) >> 1
        pixelBit4 = (y & 2) >> 1
        pixelBit5 = (z & 2) >> 1
        pixelBit6 = (x & 4) >> 2
        pixelBit7 = (y & 4) >> 2
    else:
        if microTileType != 0:
            pixelBit0 = x & 1
            pixelBit1 = y & 1
            pixelBit2 = (x & 2) >> 1
            pixelBit3 = (y & 2) >> 1
            pixelBit4 = (x & 4) >> 2
            pixelBit5 = (y & 4) >> 2
        else:
            v8 = bpp - 8
            if bpp == 0x08:
                pixelBit0 = x & 1
                pixelBit1 = (x & 2) >> 1
                pixelBit2 = (x & 4) >> 2
                pixelBit3 = (y & 2) >> 1
                pixelBit4 = y & 1
                pixelBit5 = (y & 4) >> 2
            elif bpp == 0x10:
                pixelBit0 = x & 1
                pixelBit1 = (x & 2) >> 1
                pixelBit2 = (x & 4) >> 2
                pixelBit3 = y & 1
                pixelBit4 = (y & 2) >> 1
                pixelBit5 = (y & 4) >> 2
            elif (bpp == 0x20 or bpp == 0x60):
                pixelBit0 = x & 1
                pixelBit1 = (x & 2) >> 1
                pixelBit2 = y & 1
                pixelBit3 = (x & 4) >> 2
                pixelBit4 = (y & 2) >> 1
                pixelBit5 = (y & 4) >> 2
            elif bpp == 0x40:
                pixelBit0 = x & 1
                pixelBit1 = y & 1
                pixelBit2 = (x & 2) >> 1
                pixelBit3 = (x & 4) >> 2
                pixelBit4 = (y & 2) >> 1
                pixelBit5 = (y & 4) >> 2
            elif bpp == 0x80:
                pixelBit0 = y & 1
                pixelBit1 = x & 1
                pixelBit2 = (x & 2) >> 1
                pixelBit3 = (x & 4) >> 2
                pixelBit4 = (y & 2) >> 1
                pixelBit5 = (y & 4) >> 2
            else:
                pixelBit0 = x & 1
                pixelBit1 = (x & 2) >> 1
                pixelBit2 = y & 1
                pixelBit3 = (x & 4) >> 2
                pixelBit4 = (y & 2) >> 1
                pixelBit5 = (y & 4) >> 2
        if thickness > 1:
            pixelBit6 = z & 1
            pixelBit7 = (z & 2) >> 1
    if thickness == 8:
        pixelBit8 = (z & 4) >> 2
    return (pixelBit8 << 8) | (pixelBit7 << 7) | (pixelBit6 << 6) | 32 * pixelBit5 | 16 * pixelBit4 | 8 * pixelBit3 | 4 * pixelBit2 | pixelBit0 | 2 * pixelBit1

def AddrLib_computeSurfaceAddrFromCoordLinear(x, y, slice, sample, bpp, pitch, height, numSlices, pBitPosition):
    v9 = x + pitch * y + (slice + numSlices * sample) * height * pitch

    addr = v9 * bpp

    pBitPosition = v9 * bpp % 8
    return addr // 8

def AddrLib_computeSurfaceAddrFromCoordMicroTiled(x, y, slice, bpp, pitch, height, tileMode, isDepth, tileBase, compBits, pBitPosition):
    v14 = tileMode
    if tileMode == 3:
        microTileThickness = 4
    else:
        microTileThickness = 1
    microTileBytes = microTileThickness * (((bpp << 6) + 7) >> 3)
    microTilesPerRow = pitch >> 3
    microTileIndexX = x >> 3
    microTileIndexY = y >> 3
    microTileOffset = microTileThickness * (((bpp << 6) + 7) >> 3) * (x >> 3 + (pitch >> 3) * (y >> 3))
    sliceBytes = (height * pitch * microTileThickness * bpp + 7) // 8
    sliceOffset = sliceBytes * (slice // microTileThickness)
    v12 = AddrLib_getTileType(isDepth)
    pixelIndex = AddrLib_computePixelIndexWithinMicroTile(x, y, slice, bpp, tileMode, v12)
    if (compBits != 0 and compBits != bpp and isDepth!= 0):
        pixelOffset = tileBase + compBits * pixelIndex
    else:
        pixelOffset = bpp * pixelIndex
    pBitPosition = pixelOffset % 8
    pixelOffset >>= 3
    return pixelOffset + microTileOffset + sliceOffset

def AddrLib_computeSurfaceAddrFromCoordMacroTiled(x, y, slice, sample, bpp, pitch, height, numSamples, tileMode, isDepth, tileBase, compBits, pipeSwizzle, bankSwizzle, pBitPosition):
    # numSamples is used for AA surfaces and can be set to 1 for all others
    numPipes = m_pipes
    numBanks = m_banks
    numGroupBits = m_pipeInterleaveBytesBitcount
    numPipeBits = m_pipesBitcount
    numBankBits = m_banksBitcount
    microTileThickness = computeSurfaceThickness(tileMode)
    microTileBits = numSamples * bpp * (microTileThickness * (8*8))
    microTileBytes = microTileBits >> 3
    microTileType = (1 if isDepth != 0 else 0)
    pixelIndex = computePixelIndexWithinMicroTile(x, y, slice, bpp, tileMode, microTileType)
    if isDepth != 0:
        if (compBits != 0 and compBits != bpp):
            sampleOffset = tileBase + compBits * sample
            pixelOffset = numSamples * compBits * pixelIndex
        else:
            sampleOffset = bpp * sample
            pixelOffset = numSamples * bpp * pixelIndex
    else:
        sampleOffset = sample * (microTileBits // numSamples)
        pixelOffset = bpp * pixelIndex
    elemOffset = pixelOffset + sampleOffset
    pBitPosition = (pixelOffset + sampleOffset) % 8
    bytesPerSample = microTileBytes // numSamples
    if (numSamples <= 1 or microTileBytes <= m_splitSize):
        samplesPerSlice = numSamples
        numSampleSplits = 1
        sampleSlice = 0
    else:
        samplesPerSlice = m_splitSize // bytesPerSample
        numSampleSplits = numSamples // samplesPerSlice
        numSamples = samplesPerSlice
        tileSliceBits = microTileBits // numSampleSplits
        sampleSlice = elemOffset // (microTileBits // numSampleSplits)
        elemOffset %= microTileBits // numSampleSplits
    elemOffset >>= 3
    pipe = computePipeFromCoordWoRotation(x, y)
    bank = computeBankFromCoordWoRotation(x, y)
    bankPipe = pipe + numPipes * bank
    rotation = computeSurfaceRotationFromTileMode(tileMode)
    swizzle = pipeSwizzle + numPipes * bankSwizzle
    sliceIn = slice
    if isThickMacroTiled(tileMode) != 0:
        sliceIn >>= 2
    bankPipe ^= numPipes * sampleSlice * ((numBanks >> 1) + 1) ^ (swizzle + sliceIn * rotation)
    bankPipe %= numPipes * numBanks
    pipe = bankPipe % numPipes
    bank = bankPipe // numPipes
    sliceBytes = (height * pitch * microTileThickness * bpp * numSamples + 7) // 8
    sliceOffset = sliceBytes * ((sampleSlice + numSampleSplits * slice) // microTileThickness)
    macroTilePitch = 8 * m_banks
    macroTileHeight = 8 * m_pipes
    v18 = tileMode - 5
    if (tileMode == 5 or tileMode == 9): # GX2_TILE_MODE_2D_TILED_THIN4 and GX2_TILE_MODE_2B_TILED_THIN2
        macroTilePitch >>= 1
        macroTileHeight *= 2
    elif (tileMode == 6 or tileMode == 10): # GX2_TILE_MODE_2D_TILED_THIN4 and GX2_TILE_MODE_2B_TILED_THIN4
        macroTilePitch >>= 2
        macroTileHeight *= 4
    macroTilesPerRow = pitch // macroTilePitch
    macroTileBytes = (numSamples * microTileThickness * bpp * macroTileHeight * macroTilePitch + 7) >> 3
    macroTileIndexX = x // macroTilePitch
    macroTileIndexY = y // macroTileHeight
    macroTileOffset = (x // macroTilePitch + pitch // macroTilePitch * (y // macroTileHeight)) * macroTileBytes
    if (tileMode == 8 or tileMode == 9 or tileMode == 10 or tileMode == 11 or tileMode == 14 or tileMode == 15):
        bankSwapWidth = computeSurfaceBankSwappedWidth(tileMode, bpp, numSamples, pitch, 0)
        swapIndex = macroTilePitch * macroTileIndexX // bankSwapWidth
        if m_banks > 4:
            import pywin.debugger; pywin.debugger.brk() # todo
        bankMask = m_banks-1
        bank ^= bankSwapOrder(swapIndex & bankMask)
    p4 = (pipe << numGroupBits)
    p5 = (bank << (numPipeBits + numGroupBits))
    numSwizzleBits = (numBankBits + numPipeBits)
    ukn1 = ((macroTileOffset + sliceOffset) >> numSwizzleBits)
    ukn2 = ~((1 << numGroupBits) - 1)
    ukn3 = ((elemOffset + ukn1) & ukn2)
    groupMask = ((1 << numGroupBits) - 1)
    offset1 = (macroTileOffset + sliceOffset)
    ukn4 = (elemOffset + (offset1 >> numSwizzleBits))
 
    subOffset1 = (ukn3 << numSwizzleBits)
    subOffset2 = groupMask & ukn4
 
    return subOffset1 | subOffset2 | p4 | p5

def addrLib_computeTileDataWidthAndHeight(bpp, cacheBits, pTileInfo, pMacroWidth, pMacroHeight):
    height = 1
    width = cacheBits // bpp
    pipes = m_pipes
    while (width > (pipes * 2 * height) and (width & 1) == 0):
        width >>= 1
        height *= 2
    pMacroWidth = 8 * width
    pMacroHeight = pipes * 8 * height

def AddrLib_computeCmaskBytes(pitch, height, numSlices):
    return (4 * height * pitch * numSlices + 7) // 8 // 64

def AddrLib__ComputeCmaskBaseAlign(pTileInfo):
    print("AddrLib__ComputeCmaskBaseAlign(): Uknown")
    v2 = 1 # uknown
    return m_pipeInterleaveBytes * v2

def AddrLib_computeCmaskInfo(pitchIn, heightIn, numSlices, isLinear, pTileInfo, pPitchOut, pHeightOut, pCmaskBytes, pMacroWidth, pMacroHeight, pBaseAlign, pBlockMax):
    bpp = 4
    cacheBits = 1024
    returnCode = 0
    if isLinear != 0:
        import pywin.debugger; pywin.debugger.brk()
    else:
        addrLib_computeTileDataWidthAndHeight(bpp, cacheBits, pTileInfo, macroWidth, macroHeight)
    pPitchOut = ~(macroWidth - 1) & (pitchIn + macroWidth - 1)
    pHeightOut = ~(macroHeight - 1) & (heightIn + macroHeight - 1)
    sliceBytes = AddrLib_computeCmaskBytes(pPitchOut, pHeightOut, 1)
    baseAlign = AddrLib__ComputeCmaskBaseAlign(pTileInfo)
    while 1:
        v14 = sliceBytes % baseAlign
        if not (sliceBytes % baseAlign != 0):
            break
        pHeightOut += macroHeight
        sliceBytes = AddrLib_computeCmaskBytes(pPitchOut, pHeightOut, 1)
    surfBytes = sliceBytes * numSlices
    pCmaskBytes = surfBytes
    pMacroWidth = macroWidth
    pMacroHeight = macroHeight
    pBaseAlign = baseAlign
    slice = pHeightOut * pPitchOut
    blockMax = (slice >> 14) - 1
    # uknown part possibly missing here
    pBlockMax = blockMax
    return returnCode

def main():
    """
    This place is a mess...
    """
    print("GTX Extractor v1.4")
    print("(C) 2014 Treeki, 2015-2016 AboodXD")
    
    if len(sys.argv) != 2:
        print("")
        print("Usage (If converting from .gtx to png, and using source code): python gtx_extract.py input")
        print("Usage (If converting from .gtx to png, and using exe): gtx_extract.exe input")
        print("Usage (If converting from png to .gtx, and using source code): python gtx_extract.py input(.png) input(.gtx)")
        print("Usage (If converting from png to .gtx, and using exe): gtx_extract.exe input(png) input(.gtx)")
        print("")
        print("Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)
    
    with open(sys.argv[1], "rb") as inf:
        print('Converting: ' + sys.argv[1])
        inb = inf.read()
        inf.close()
    
    data = readGFD(inb)

    print("")
    print("// ----- GX2Surface Info ----- ")
    #print("  index     = " + str(0))
    print("  dim       = " + str(data.dim))
    print("  width     = " + str(data.width))
    print("  height    = " + str(data.height))
    print("  depth     = " + str(data.depth))
    print("  numMips   = " + str(data.numMips))
    if data.format in formats:
        print("  format    = " + formats[data.format])
    else:
        print("  format    = " + hex(data.format))
    print("  aa        = " + str(data.aa))
    print("  use       = " + str(data.use))
    print("  imageSize = " + str(data.imageSize))
    print("  mipSize   = " + str(data.mipSize))
    print("  tileMode  = " + str(data.tileMode))
    print("  swizzle   = " + str(data.swizzle) + ", " + hex(data.swizzle))
    print("  alignment = " + str(data.alignment))
    print("  pitch     = " + str(data.pitch))
    #print("  mipOffset = " + str(data.mipOffset))
    
    name = os.path.splitext(sys.argv[1])[0]

    for img in writePNG(data):
        img.save(name + ".png")
        print('')
        print('Finished converting: ' + sys.argv[1])

if __name__ == '__main__': main()
