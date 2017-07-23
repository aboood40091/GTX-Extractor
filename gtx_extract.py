#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# GTX Extractor
# Version v5.1
# Copyright © 2014 Treeki, 2015-2017 Stella/AboodXD

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

"""gtx_extract.py: Decode GTX images."""

import os
import struct
import sys
import time

try:
    import addrlib_cy as addrlib
except ImportError:
    import addrlib

import dds

__author__ = "AboodXD"
__copyright__ = "Copyright 2014 Treeki, 2015-2017 Stella/AboodXD"
__credits__ = ["Stella/AboodXD", "Treeki", "AddrLib", "Exzap"]

formats = {0x00000000: 'GX2_SURFACE_FORMAT_INVALID',
           0x0000001a: 'GX2_SURFACE_FORMAT_TCS_R8_G8_B8_A8_UNORM',
           0x0000041a: 'GX2_SURFACE_FORMAT_TCS_R8_G8_B8_A8_SRGB',
           0x00000019: 'GX2_SURFACE_FORMAT_TCS_R10_G10_B10_A2_UNORM',
           0x00000008: 'GX2_SURFACE_FORMAT_TCS_R5_G6_B5_UNORM',
           0x0000000a: 'GX2_SURFACE_FORMAT_TC_R5_G5_B5_A1_UNORM',
           0x0000000b: 'GX2_SURFACE_FORMAT_TC_R4_G4_B4_A4_UNORM',
           0x00000001: 'GX2_SURFACE_FORMAT_TC_R8_UNORM',
           0x00000007: 'GX2_SURFACE_FORMAT_TC_R8_G8_UNORM',
           0x00000002: 'GX2_SURFACE_FORMAT_TC_R4_G4_UNORM',
           0x00000031: 'GX2_SURFACE_FORMAT_T_BC1_UNORM',
           0x00000431: 'GX2_SURFACE_FORMAT_T_BC1_SRGB',
           0x00000032: 'GX2_SURFACE_FORMAT_T_BC2_UNORM',
           0x00000432: 'GX2_SURFACE_FORMAT_T_BC2_SRGB',
           0x00000033: 'GX2_SURFACE_FORMAT_T_BC3_UNORM',
           0x00000433: 'GX2_SURFACE_FORMAT_T_BC3_SRGB',
           0x00000034: 'GX2_SURFACE_FORMAT_T_BC4_UNORM',
           0x00000234: 'GX2_SURFACE_FORMAT_T_BC4_SNORM',
           0x00000035: 'GX2_SURFACE_FORMAT_T_BC5_UNORM',
           0x00000235: 'GX2_SURFACE_FORMAT_T_BC5_SNORM'
           }

BCn_formats = [0x31, 0x431, 0x32, 0x432, 0x33, 0x433, 0x34, 0x234, 0x35, 0x235]


class GFDData:
    pass


class GFDHeader(struct.Struct):
    def __init__(self):
        super().__init__('>4s7I')

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
        super().__init__('>4s7I')

    def data(self, data, pos):
        (self.magic,
         self.size_,
         self.majorVersion,
         self.minorVersion,
         self.type_,
         self.dataSize,
         self.id,
         self.typeIdx) = self.unpack_from(data, pos)


class GX2Surface(struct.Struct):
    def __init__(self):
        super().__init__('>16I')

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
         self.pitch) = self.unpack_from(data, pos)


def swapRB(bgra):
    return bytes((bgra[2], bgra[1], bgra[0], bgra[3]))


def readGFD(f):
    gfd = GFDData()

    pos = 0

    header = GFDHeader()
    header.data(f, pos)

    if header.magic != b'Gfx2':
        raise ValueError("Invalid file header!")

    pos += header.size

    blockB = False
    blockC = False

    images = 0
    imgInfo = 0

    gfd.dim = []
    gfd.width = []
    gfd.height = []
    gfd.depth = []
    gfd.numMips = []
    gfd.format = []
    gfd.aa = []
    gfd.use = []
    gfd.imageSize = []
    gfd.imagePtr = []
    gfd.mipSize = []
    gfd.mipPtr = []
    gfd.tileMode = []
    gfd.swizzle = []
    gfd.alignment = []
    gfd.pitch = []
    gfd.compSel = []
    gfd.surfOut = []
    gfd.realSize = []

    gfd.dataSize = []
    gfd.data = []

    while pos < len(f):  # Loop through the entire file, stop if reached the end of the file.
        block = GFDBlockHeader()
        block.data(f, pos)

        if block.magic != b'BLK{':
            raise ValueError("Invalid block header!")

        pos += block.size

        if block.type_ == 0x0B:
            imgInfo += 1
            blockB = True

            surface = GX2Surface()
            surface.data(f, pos)

            pos += surface.size
            pos += 68

            compSel = []
            for i in range(4):
                compSel.append(f[pos + i])

            pos += 24

            if surface.format_ in BCn_formats:
                width = surface.width // 4
                height = surface.height // 4
            else:
                width = surface.width
                height = surface.height

            surfOut = addrlib.getSurfaceInfo(surface.format_, width, height, surface.depth, surface.dim, surface.tileMode, surface.aa, 0)

            gfd.dim.append(surface.dim)
            gfd.width.append(surface.width)
            gfd.height.append(surface.height)
            gfd.depth.append(surface.depth)
            gfd.numMips.append(surface.numMips)
            gfd.format.append(surface.format_)
            gfd.aa.append(surface.aa)
            gfd.use.append(surface.use)
            gfd.imageSize.append(surface.imageSize)
            gfd.imagePtr.append(surface.imagePtr)
            gfd.mipSize.append(surface.mipSize)
            gfd.mipPtr.append(surface.mipPtr)
            gfd.tileMode.append(surface.tileMode)
            gfd.swizzle.append(surface.swizzle)
            gfd.alignment.append(surface.alignment)
            gfd.pitch.append(surfOut.pitch)
            gfd.compSel.append(compSel)
            gfd.surfOut.append(surfOut)
            if surface.format_ in BCn_formats:
                gfd.realSize.append(((surface.width + 3) >> 2) * ((surface.height + 3) >> 2) * (
                    addrlib.surfaceGetBitsPerPixel(surface.format_) // 8))
            else:
                gfd.realSize.append(
                    surface.width * surface.height * (addrlib.surfaceGetBitsPerPixel(surface.format_) // 8))

        elif block.type_ == 0x0C:
            images += 1
            blockC = True

            gfd.dataSize.append(block.dataSize)
            gfd.data.append(f[pos:pos + block.dataSize])
            pos += block.dataSize

        else:
            pos += block.dataSize

    if images != imgInfo:
        print("")
        print("Whoops, fail! XD")
        print("")
        print("Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    if blockB:
        if not blockC:
            print("")
            print("Image info was found but no Image data was found.")
            print("")
            print("Exiting in 5 seconds...")
            time.sleep(5)
            sys.exit(1)
    if not blockB:
        if not blockC:
            print("")
            print("No Image was found in this file.")
            print("")
            print("Exiting in 5 seconds...")
            time.sleep(5)
            sys.exit(1)
        elif blockC:
            print("")
            print("Image data was found but no Image info was found.")
            print("")
            print("Exiting in 5 seconds...")
            time.sleep(5)
            sys.exit(1)

    gfd.numImages = images

    return gfd


def get_deswizzled_data(i, numImages, width, height, depth, dim, format_, aa, tileMode, swizzle_, pitch, compSel, data, size, surfOut):
    if format_ in formats:
        if aa != 0:
            print("")
            print("Unsupported aa!")
            if i != (numImages - 1):
                print("Continuing in 5 seconds...")
                time.sleep(5)
                return b'', b''
            else:
                print("Exiting in 5 seconds...")
                time.sleep(5)
                sys.exit(1)

        if format_ == 0x00:
            print("")
            print("Invalid texture format!")
            if i != (numImages - 1):
                print("Continuing in 5 seconds...")
                time.sleep(5)
                return b'', b''
            else:
                print("Exiting in 5 seconds...")
                time.sleep(5)
                sys.exit(1)

        else:
            if format_ == 0x1a or format_ == 0x41a:
                format__ = 28
            elif format_ == 0x19:
                format__ = 24
            elif format_ == 0x8:
                format__ = 85
            elif format_ == 0xa:
                format__ = 86
            elif format_ == 0xb:
                format__ = 115
            elif format_ == 0x1:
                format__ = 61
            elif format_ == 0x7:
                format__ = 49
            elif format_ == 0x2:
                format__ = 112
            elif format_ == 0x31 or format_ == 0x431:
                format__ = "BC1"
            elif format_ == 0x32 or format_ == 0x432:
                format__ = "BC2"
            elif format_ == 0x33 or format_ == 0x433:
                format__ = "BC3"
            elif format_ == 0x34:
                format__ = "BC4U"
            elif format_ == 0x234:
                format__ = "BC4S"
            elif format_ == 0x35:
                format__ = "BC5U"
            elif format_ == 0x235:
                format__ = "BC5S"

            if surfOut.depth != 1:
                print("")
                print("Unsupported depth!")
                if i != (numImages - 1):
                    print("Continuing in 5 seconds...")
                    time.sleep(5)
                    return b'', b''
                else:
                    print("Exiting in 5 seconds...")
                    time.sleep(5)
                    sys.exit(1)

            result = addrlib.deswizzle(width, height, surfOut.height, format_, surfOut.tileMode, swizzle_, pitch, surfOut.bpp, data)
            result = result[:size]

            hdr = dds.generateHeader(1, width, height, format__, compSel, size, format_ in BCn_formats)

    else:
        print("")
        print("Unsupported texture format_: " + hex(format_))
        if i != (numImages - 1):
            print("Continuing in 5 seconds...")
            time.sleep(5)
            hdr, result = b'', b''
        else:
            print("Exiting in 5 seconds...")
            time.sleep(5)
            sys.exit(1)

    return hdr, result


def writeGFD(f, tileMode, swizzle_, SRGB):
    width, height, format_, dataSize, compSel, data = dds.readDDS(f, SRGB)

    if format_ in BCn_formats:
        width_ = (width + 3) >> 2
        height_ = (height + 3) >> 2
        if format_ in [0x31, 0x431, 0x234, 0x34]:
            align = 0xEE4
        else:
            align = 0x1EE4
    else:
        width_ = width
        height_ = height
        align = 0x6E4

    bpp = addrlib.surfaceGetBitsPerPixel(format_) >> 3

    alignment = 512 * bpp

    surfOut = addrlib.getSurfaceInfo(format_, width_, height_, 1, 1, tileMode, 0, 0)

    padSize = surfOut.surfSize - dataSize
    data += padSize * b"\x00"

    if surfOut.depth != 1:
        print("")
        print("Unsupported depth!")
        print("Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    if tileMode in [1, 2, 3, 16]:
        s = 0
    else:
        s = 0xd0000

    s |= swizzle_ << 8

    compSels = ["Red", "Green", "Blue", "Alpha", "0", "1"]

    print("")
    print("// ----- GX2Surface Info ----- ")
    print("  dim             = 1")
    print("  width           = " + str(width))
    print("  height          = " + str(height))
    print("  depth           = 1")
    print("  numMips         = 1")
    print("  format          = " + formats[format_])
    print("  aa              = 0")
    print("  use             = 1")
    print("  imageSize       = " + str(len(data)))
    print("  mipSize         = 0")
    print("  tileMode        = " + str(tileMode))
    print("  swizzle         = " + str(s) + ", " + hex(s))
    print("  alignment       = " + str(alignment))
    print("  pitch           = " + str(surfOut.pitch))
    print("")
    print("  GX2 Component Selector:")
    print("    Channel 1:      " + str(compSels[compSel[0]]))
    print("    Channel 2:      " + str(compSels[compSel[1]]))
    print("    Channel 3:      " + str(compSels[compSel[2]]))
    print("    Channel 4:      " + str(compSels[compSel[3]]))
    print("")
    print("  bits per pixel  = " + str(bpp << 3))
    print("  bytes per pixel = " + str(bpp))
    print("  realSize        = " + str(dataSize))

    swizzled_data = addrlib.swizzle(width, height, surfOut.height, format_, surfOut.tileMode, s, surfOut.pitch, surfOut.bpp, data)

    head_struct = GFDHeader()
    head = head_struct.pack(b"Gfx2", 32, 7, 1, 2, 1, 0, 0)

    block_head_struct = GFDBlockHeader()
    gx2surf_blk_head = block_head_struct.pack(b"BLK{", 32, 1, 0, 0xb, 0x9c, 0, 0)

    gx2surf_struct = GX2Surface()
    gx2surf = gx2surf_struct.pack(1, width, height, 1, 1, format_, 0, 1, len(swizzled_data), 0, 0, 0, tileMode, s, alignment, surfOut.pitch)

    align_blk_head = block_head_struct.pack(b"BLK{", 32, 1, 0, 2, align, 0, 0)

    image_blk_head = block_head_struct.pack(b"BLK{", 32, 1, 0, 0xc, len(swizzled_data), 0, 0)

    eof_blk_head = block_head_struct.pack(b"BLK{", 32, 1, 0, 1, 0, 0, 0)

    output = head + gx2surf_blk_head + gx2surf
    output += b"\x00" * 56
    output += 1 .to_bytes(4, 'big')
    output += b"\x00" * 4
    output += 1 .to_bytes(4, 'big')

    for value in compSel:
        output += value.to_bytes(1, 'big')

    output += b"\x00" * 20
    output += align_blk_head
    output += b"\x00" * align
    output += image_blk_head
    output += swizzled_data
    output += eof_blk_head

    return output


def printInfo():
    print("")
    print("Usage:")
    print("  gtx_extract [option...] input")
    print("")
    print("Options:")
    print(" -o <output>           Output file, if not specified, the output file will have the same name as the intput file")
    print("                       Will be ignored if the GTX has multiple images")
    print("")
    print("DDS to GTX options:")
    print(" -tileMode <tileMode>  tileMode (4 is the default)")
    print(" -swizzle <swizzle>    the intial swizzle value, a value from 0 to 7 (0 is the default)")
    print(" -SRGB <n>             1 if the desired destination format is SRGB, else 0 (0 is the default)")
    print("")
    print("Supported formats:")
    print(" - GX2_SURFACE_FORMAT_TCS_R8_G8_B8_A8_UNORM")
    print(" - GX2_SURFACE_FORMAT_TCS_R8_G8_B8_A8_SRGB")
    print(" - GX2_SURFACE_FORMAT_TCS_R10_G10_B10_A2_UNORM")
    print(" - GX2_SURFACE_FORMAT_TCS_R5_G6_B5_UNORM")
    print(" - GX2_SURFACE_FORMAT_TC_R5_G5_B5_A1_UNORM")
    print(" - GX2_SURFACE_FORMAT_TC_R4_G4_B4_A4_UNORM")
    print(" - GX2_SURFACE_FORMAT_TC_R8_UNORM")
    print(" - GX2_SURFACE_FORMAT_TC_R8_G8_UNORM")
    print(" - GX2_SURFACE_FORMAT_TC_R4_G4_UNORM")
    print(" - GX2_SURFACE_FORMAT_T_BC1_UNORM")
    print(" - GX2_SURFACE_FORMAT_T_BC1_SRGB")
    print(" - GX2_SURFACE_FORMAT_T_BC2_UNORM")
    print(" - GX2_SURFACE_FORMAT_T_BC2_SRGB")
    print(" - GX2_SURFACE_FORMAT_T_BC3_UNORM")
    print(" - GX2_SURFACE_FORMAT_T_BC3_SRGB")
    print(" - GX2_SURFACE_FORMAT_T_BC4_UNORM")
    print(" - GX2_SURFACE_FORMAT_T_BC4_SNORM")
    print(" - GX2_SURFACE_FORMAT_T_BC5_UNORM")
    print(" - GX2_SURFACE_FORMAT_T_BC5_SNORM")
    print("")
    print("Exiting in 5 seconds...")
    time.sleep(5)
    sys.exit(1)


def main():
    print("GTX Extractor v5.1")
    print("(C) 2014 Treeki, 2015-2017 Stella/AboodXD")

    input_ = sys.argv[-1]

    if not (input_.endswith('.gtx') or input_.endswith('.dds')):
        printInfo()

    toGTX = False

    if input_.endswith('.dds'):
        toGTX = True

    if "-o" in sys.argv:
        output_ = sys.argv[sys.argv.index("-o") + 1]
    else:
        output_ = os.path.splitext(input_)[0] + (".gtx" if toGTX else ".dds")

    print("")
    print('Converting: ' + input_)

    if toGTX:
        if "-tileMode" in sys.argv:
            tileMode = int(sys.argv[sys.argv.index("-tileMode") + 1], 0)
        else:
            tileMode = 4

        if "-swizzle" in sys.argv:
            swizzle = int(sys.argv[sys.argv.index("-swizzle") + 1], 0)
        else:
            swizzle = 0

        if "-SRGB" in sys.argv:
            SRGB = int(sys.argv[sys.argv.index("-SRGB") + 1], 0)
        else:
            SRGB = 0

        if SRGB > 1 or not 0 <= tileMode <= 16 or not 0 <= swizzle <= 7:
            printInfo()

        data = writeGFD(input_, tileMode, swizzle, SRGB)

        with open(output_, "wb+") as output:
            output.write(data)

    else:
        with open(input_, "rb") as inf:
            inb = inf.read()

        compSel = ["Red", "Green", "Blue", "Alpha", "0", "1"]

        gfd = readGFD(inb)

        for i in range(gfd.numImages):

            print("")
            print("// ----- GX2Surface Info ----- ")
            print("  dim             = " + str(gfd.dim[i]))
            print("  width           = " + str(gfd.width[i]))
            print("  height          = " + str(gfd.height[i]))
            print("  depth           = " + str(gfd.depth[i]))
            print("  numMips         = " + str(gfd.numMips[i]))
            if gfd.format[i] in formats:
                print("  format          = " + formats[gfd.format[i]])
            else:
                print("  format          = " + hex(gfd.format[i]))
            print("  aa              = " + str(gfd.aa[i]))
            print("  use             = " + str(gfd.use[i]))
            print("  imageSize       = " + str(gfd.imageSize[i]))
            print("  mipSize         = " + str(gfd.mipSize[i]))
            print("  tileMode        = " + str(gfd.tileMode[i]))
            print("  swizzle         = " + str(gfd.swizzle[i]) + ", " + hex(gfd.swizzle[i]))
            print("  alignment       = " + str(gfd.alignment[i]))
            print("  pitch           = " + str(gfd.pitch[i]))
            bpp = addrlib.surfaceGetBitsPerPixel(gfd.format[i])
            print("")
            print("  GX2 Component Selector:")
            print("    Channel 1:      " + str(compSel[gfd.compSel[i][0]]))
            print("    Channel 2:      " + str(compSel[gfd.compSel[i][1]]))
            print("    Channel 3:      " + str(compSel[gfd.compSel[i][2]]))
            print("    Channel 4:      " + str(compSel[gfd.compSel[i][3]]))
            print("")
            print("  bits per pixel  = " + str(bpp))
            print("  bytes per pixel = " + str(bpp // 8))
            print("  realSize        = " + str(gfd.realSize[i]))

            if gfd.numImages > 1:
                output_  = os.path.splitext(input_)[0] + str(i) + ".dds"

            hdr, data = get_deswizzled_data(i, gfd.numImages, gfd.width[i], gfd.height[i], gfd.depth[i], gfd.dim[i],
                                            gfd.format[i],gfd.aa[i], gfd.tileMode[i], gfd.swizzle[i], gfd.pitch[i],
                                            gfd.compSel[i], gfd.data[i], gfd.realSize[i], gfd.surfOut[i])

            if data == b'':
                pass
            else:
                with open(output_, "wb+") as output:
                    output.write(hdr)
                    output.write(data)

    print('')
    print('Finished converting: ' + input_)


if __name__ == '__main__':
    main()
