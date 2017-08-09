#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# GTX Extractor
# Version v5.2
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

try:
    import form_conv_cy as form_conv
except ImportError:
    import form_conv

__author__ = "Stella/AboodXD"
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
    gfd.realSize = []

    gfd.dataSize = []
    gfd.data = []

    gfd.mipOffsets = []
    gfd.mipData = {}

    while pos < len(f):  # Loop through the entire file, stop if reached the end of the file.
        block = GFDBlockHeader()
        block.data(f, pos)

        if block.magic != b'BLK{':
            print(block.magic)
            print(pos)
            raise ValueError("Invalid block header!")

        pos += block.size

        if block.type_ == 0x0B:
            imgInfo += 1
            blockB = True

            surface = GX2Surface()
            surface.data(f, pos)

            pos += surface.size

            if surface.numMips > 14:
                print("")
                print("Invalid number of mipmaps for image " + str(imgInfo - 1))
                print("")
                print("Exiting in 5 seconds...")
                time.sleep(5)
                sys.exit(1)

            mipOffsets = []
            for i in range(13):
                mipOffsets.append(f[i * 4 + pos] << 24 | f[i * 4 + 1 + pos] << 16 | f[i * 4 + 2 + pos] << 8 | f[i * 4 + 3 + pos])

            gfd.mipOffsets.append(mipOffsets)
            
            pos += 68

            compSel = []
            for i in range(4):
                comp = f[pos + i]
                if comp == 4: # Sorry, but this is unsupported.
                    comp = i
                compSel.append(f[pos + i])

            pos += 24

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
            gfd.pitch.append(surface.pitch)
            gfd.compSel.append(compSel)
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

        elif block.type_ == 0x0D:
            gfd.mipData[images - 1] = f[pos:pos + block.dataSize]
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


def get_deswizzled_data(i, gfd):
    numImages = gfd.numImages
    numMips = gfd.numMips[i]
    width = gfd.width[i]
    height = gfd.height[i]
    depth = gfd.depth[i]
    dim = gfd.dim[i]
    format_ = gfd.format[i]
    aa = gfd.aa[i]
    tileMode = gfd.tileMode[i]
    swizzle_ = gfd.swizzle[i]
    compSel = gfd.compSel[i]
    data = gfd.data[i]
    mipSize = gfd.mipSize[i]
    realSize = gfd.realSize[i]
    surfOut = addrlib.getSurfaceInfo(format_, width, height, depth, dim, tileMode, aa, 0)
    bpp = (surfOut.bpp + 7) // 8
    mipOffsets = gfd.mipOffsets[i]

    try:
        mipData = gfd.mipData[i]
    except KeyError:
        mipData = b''

    if format_ in formats:
        if aa != 0:
            print("")
            print("Unsupported aa!")
            print("")
            if i != (numImages - 1):
                print("Continuing in 5 seconds...")
                time.sleep(5)
                return b'', []
            else:
                print("Exiting in 5 seconds...")
                time.sleep(5)
                sys.exit(1)

        if format_ == 0x00:
            print("")
            print("Invalid texture format!")
            print("")
            if i != (numImages - 1):
                print("Continuing in 5 seconds...")
                time.sleep(5)
                return b'', []
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
                print("")
                if i != (numImages - 1):
                    print("Continuing in 5 seconds...")
                    time.sleep(5)
                    return b'', b'', b''
                else:
                    print("Exiting in 5 seconds...")
                    time.sleep(5)
                    sys.exit(1)

            print("")
            print("Processing " + str(numMips - 1) + " mipmaps:")

            result = []
            for level in range(numMips):
                if format_ in BCn_formats:
                    size = ((max(1, width >> level) + 3) >> 2) * ((max(1, height >> level) + 3) >> 2) * bpp
                else:
                    size = max(1, width >> level) * max(1, height >> level) * bpp

                if level != 0:
                    print(str(level) + ": " + str(max(1, width >> level)) + "x" + str(max(1, height >> level)))

                    if level == 1:
                        mipOffset = mipOffsets[level - 1] - surfOut.surfSize
                    else:
                        mipOffset = mipOffsets[level - 1]

                    surfOut = addrlib.getSurfaceInfo(format_, width, height, depth, dim, tileMode, aa, level)

                    data = mipData[mipOffset:mipOffset + surfOut.surfSize]

                deswizzled = addrlib.deswizzle(max(1, width >> level), max(1, height >> level), surfOut.height, format_, surfOut.tileMode, swizzle_, surfOut.pitch, surfOut.bpp, data)

                if format_ == 0xa:
                    data = form_conv.toDDSrgb5a1(deswizzled[:size])

                elif format_ == 0xb:
                    data = form_conv.toDDSrgba4(deswizzled[:size])

                else:
                    data = deswizzled[:size]

                result.append(data)

            hdr = dds.generateHeader(numMips, width, height, format__, compSel, realSize, format_ in BCn_formats)

    else:
        print("")
        print("Unsupported texture format_: " + hex(format_))
        print("")
        if i != (numImages - 1):
            print("Continuing in 5 seconds...")
            time.sleep(5)
            hdr, result = b'', []
        else:
            print("Exiting in 5 seconds...")
            time.sleep(5)
            sys.exit(1)

    return hdr, result


def get_curr_mip_off_size(width, height, bpp, curr_level, compressed):
    off = 0

    for i in range(curr_level - 1):
        level = i + 1
        if compressed:
            off += ((max(1, width >> level) + 3) >> 2) * ((max(1, height >> level) + 3) >> 2) * bpp
        else:
            off += max(1, width >> level) * max(1, height >> level) * bpp

    if compressed:
        size = ((max(1, width >> curr_level) + 3) >> 2) * ((max(1, height >> curr_level) + 3) >> 2) * bpp
    else:
        size = max(1, width >> curr_level) * max(1, height >> curr_level) * bpp

    return off, size


def writeGFD(f, tileMode, swizzle_, SRGB, n, numImages):
    width, height, format_, fourcc, dataSize, compSel, numMips, data = dds.readDDS(f, SRGB)

    if 0 in [width, dataSize] and data == []:
        print("")
        if n != (numImages - 1):
            print("Continuing in 5 seconds...")
            time.sleep(5)
            return b''
        else:
            print("Exiting in 5 seconds...")
            time.sleep(5)
            sys.exit(1)

    if format_ not in formats:
        print("")
        print("Unsupported DDS format!")
        print("")
        if n != (numImages - 1):
            print("")
            print("Continuing in 5 seconds...")
            time.sleep(5)
            return b''
        else:
            print("Exiting in 5 seconds...")
            time.sleep(5)
            sys.exit(1)

    if numMips > 13:
        print("")
        print("Invalid number of mipmaps for " + f)
        print("")
        if n != (numImages - 1):
            print("")
            print("Continuing in 5 seconds...")
            time.sleep(5)
            return b''
        else:
            print("Exiting in 5 seconds...")
            time.sleep(5)
            sys.exit(1)

    imageData = data[:dataSize]
    mipData = data[dataSize:]
    numMips += 1

    if format_ in BCn_formats:
        if format_ in [0x31, 0x431, 0x234, 0x34]:
            align = 0xEE4
            mipAlign = 0xFC0
        else:
            align = 0x1EE4
            mipAlign = 0x1FC0
    else:
        align = 0x6E4
        mipAlign = 0x7C0

    bpp = addrlib.surfaceGetBitsPerPixel(format_) >> 3

    alignment = 512 * bpp

    surfOut = addrlib.getSurfaceInfo(format_, width, height, 1, 1, tileMode, 0, 0)

    pitch = surfOut.pitch

    if surfOut.depth != 1:
        print("")
        print("Unsupported depth!")
        print("")
        if n != (numImages - 1):
            print("Continuing in 5 seconds...")
            time.sleep(5)
            return b''
        else:
            print("Exiting in 5 seconds...")
            time.sleep(5)
            sys.exit(1)

    if tileMode in [1, 2, 3, 16]:
        s = 0
    else:
        s = 0xd0000

    s |= swizzle_ << 8

    if numMips > 1:
        print("")
        print("Processing " + str(numMips - 1) + " mipmaps:")

    swizzled_data = []
    imageSize = 0
    mipSize = 0
    mipOffsets = []
    for i in range(numMips):
        if i == 0:
            data = imageData

            imageSize = surfOut.surfSize
        else:
            print(str(i) + ": " + str(max(1, width >> i)) + "x" + str(max(1, height >> i)))

            offset, dataSize = get_curr_mip_off_size(width, height, bpp, i, format_ in BCn_formats)

            data = mipData[offset:offset+dataSize]

            surfOut = addrlib.getSurfaceInfo(format_, width, height, 1, 1, tileMode, 0, i)

        padSize = surfOut.surfSize - dataSize
        data += padSize * b"\x00"

        if i != 0:
            offset += padSize

            if i == 1:
                mipOffsets.append(imageSize)
            else:
                mipOffsets.append(offset)

            mipSize += len(data)

        swizzled_data.append(addrlib.swizzle(max(1, width >> i), max(1, width >> i), surfOut.height, format_, surfOut.tileMode, s, surfOut.pitch, surfOut.bpp, data))

    compSels = ["R", "G", "B", "A", "0", "1"]

    print("")
    print("// ----- GX2Surface Info ----- ")
    print("  dim             = 1")
    print("  width           = " + str(width))
    print("  height          = " + str(height))
    print("  depth           = 1")
    print("  numMips         = " + str(numMips))
    print("  format          = " + formats[format_])
    print("  aa              = 0")
    print("  use             = 1")
    print("  imageSize       = " + str(imageSize))
    print("  mipSize         = " + str(mipSize))
    print("  tileMode        = " + str(tileMode))
    print("  swizzle         = " + str(s) + ", " + hex(s))
    print("  alignment       = " + str(alignment))
    print("  pitch           = " + str(pitch))
    print("")
    print("  GX2 Component Selector:")
    print("    Red Channel:    " + str(compSels[compSel[0]]))
    print("    Green Channel:  " + str(compSels[compSel[1]]))
    print("    Blue Channel:   " + str(compSels[compSel[2]]))
    print("    Alpha Channel:  " + str(compSels[compSel[3]]))
    print("")
    print("  bits per pixel  = " + str(bpp << 3))
    print("  bytes per pixel = " + str(bpp))
    print("  realSize        = " + str(len(imageData)))

    block_head_struct = GFDBlockHeader()
    gx2surf_blk_head = block_head_struct.pack(b"BLK{", 32, 1, 0, 0xb, 0x9c, 0, 0)

    gx2surf_struct = GX2Surface()
    gx2surf = gx2surf_struct.pack(1, width, height, 1, numMips, format_, 0, 1, imageSize, 0, mipSize, 0, tileMode, s, alignment, pitch)

    align_blk_head = block_head_struct.pack(b"BLK{", 32, 1, 0, 2, align, 0, 0)

    image_blk_head = block_head_struct.pack(b"BLK{", 32, 1, 0, 0xc, imageSize, 0, 0)

    mipAlign_blk_head = block_head_struct.pack(b"BLK{", 32, 1, 0, 2, mipAlign, 0, 0)

    mip_blk_head = block_head_struct.pack(b"BLK{", 32, 1, 0, 0xd, mipSize, 0, 0)

    output = gx2surf_blk_head + gx2surf

    if numMips > 1:
        i = 0
        for offset in mipOffsets:
            output += offset.to_bytes(4, 'big')
            i += 1
        for z in range(14 - i):
            output += 0 .to_bytes(4, 'big')
    else:
        output += b"\x00" * 56

    output += numMips.to_bytes(4, 'big')
    output += b"\x00" * 4
    output += 1 .to_bytes(4, 'big')

    for value in compSel:
        output += value.to_bytes(1, 'big')

    output += b"\x00" * 20
    output += align_blk_head
    output += b"\x00" * align
    output += image_blk_head
    output += swizzled_data[0]

    if numMips > 1:
        output += mipAlign_blk_head
        output += b"\x00" * mipAlign
        output += mip_blk_head
        i = 0
        for data in swizzled_data:
            if i != 0:
                output += data
            i += 1

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
    print(" -multi <numImages>    number of images to pack into the GTX file (input file must be the first image, 1 is the default)")
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
    print("GTX Extractor v5.2")
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

        multi = False
        if "-multi" in sys.argv:
            multi = True
            numImages = int(sys.argv[sys.argv.index("-multi") + 1], 0)

        if SRGB > 1 or not 0 <= tileMode <= 16 or not 0 <= swizzle <= 7:
            printInfo()

        if "-o" not in sys.argv and "-multi" in sys.argv:
            output_ = output_[:-5] + ".gtx"

        with open(output_, "wb+") as output:
            head_struct = GFDHeader()
            head = head_struct.pack(b"Gfx2", 32, 7, 1, 2, 1, 0, 0)

            output.write(head)

            if multi:
                input_ = input_[:-5]
                for i in range(numImages):
                    print("")
                    print('Converting: ' + input_ + str(i) + ".dds")
                    
                    data = writeGFD(input_ + str(i) + ".dds", tileMode, swizzle, SRGB, i, numImages)
                    output.write(data)
            else:
                print("")
                print('Converting: ' + input_)

                data = writeGFD(input_, tileMode, swizzle, SRGB, 0, 1)
                output.write(data)

            block_head_struct = GFDBlockHeader()
            eof_blk_head = block_head_struct.pack(b"BLK{", 32, 1, 0, 1, 0, 0, 0)

            output.write(eof_blk_head)

    else:
        print("")
        print('Converting: ' + input_)

        with open(input_, "rb") as inf:
            inb = inf.read()

        compSel = ["R", "G", "B", "A", "0", "1"]

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
            print("    Red Channel:    " + str(compSel[gfd.compSel[i][0]]))
            print("    Green Channel:  " + str(compSel[gfd.compSel[i][1]]))
            print("    Blue Channel:   " + str(compSel[gfd.compSel[i][2]]))
            print("    Alpha Channel:  " + str(compSel[gfd.compSel[i][3]]))
            print("")
            print("  bits per pixel  = " + str(bpp))
            print("  bytes per pixel = " + str(bpp // 8))
            print("  realSize        = " + str(gfd.realSize[i]))

            if gfd.numImages > 1:
                output_  = os.path.splitext(input_)[0] + str(i) + ".dds"

            hdr, result = get_deswizzled_data(i, gfd)

            if hdr == b'' or result == []:
                pass
            else:
                with open(output_, "wb+") as output:
                    output.write(hdr)
                    for data in result:
                        output.write(data)

    print('')
    print('Finished converting: ' + input_)


if __name__ == '__main__':
    main()
