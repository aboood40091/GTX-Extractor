#!/usr/bin/python
# -*- coding: latin-1 -*-

# gtx_etract
# Provides functions for rendering Wii U GTX images.

# Copyright (C) 2014-2016 Treeki, RoadrunnerWMC, MrRean, Grop

# Based on GTX Extractor by Treeki

# Portions of this code are based on Wii U GTX Extractor (https://github.com/Treeki/RandomStuff):
#   (README.markdown:)
#     Wii U GTX Extractor
#
#     Extracts textures in RGBA8 and DXT5 formats from the 'Gfx2' (.gtx file extension)
#     format used in Wii U games. A bit of work could get it to extract .bflim files, too.
#
#     Somewhat unfinished, pretty buggy. Use at your own risk. It's not great, but I figured
#     I'd throw it out there to save other people the work I already did.
#
#     More details on compilation and usage in the comments inside the file.
#
#  (Header of gtx_extract.c:)
#     Wii U 'GTX' Texture Extractor
#     Created by Ninji Vahran / Treeki; 2014-10-31
#     ( https://github.com/Treeki )
#     This software is released into the public domain.
#
#     Dependencies: libtxc_dxtn, libpng
#     Tested with GCC on Arch Linux. May fail elsewhere.
#     Expect it to fail anywhere, really ;)
#
#     gcc -lpng -ltxc_dxtn -o gtx_extract gtx_extract.c
#
#     This tool currently supports RGBA8 (format 0x1A) and DXT5 (format 0x33)
#     textures.
#     The former is known to work with 2048x512 textures.
#     The latter has been tested successfully with 512x320 and 2048x512 textures,
#     and is known to be broken with 384x256 textures.
#
#     Why so complex?
#     Wii U textures appear to be packed using a complex 'texture swizzling'
#     algorithm, presumably for faster access.
#
#     With no publicly known details that I could find, I had to attempt to
#     recreate it myself - with a limited set of sample data to examine.
#
#     This tool's implementation is sufficient to unpack the textures I wanted,
#     but it's likely to fail on others.
#     Feel free to throw a pull request at me if you improve it!


# Portions of this code are based on libtxc_dxtn:
#  (No readme available.)
#  (Header of txc_fetch_dxtn.c:)
#     libtxc_dxtn
#     Version:  1.0
#
#     Copyright (C) 2004  Roland Scheidegger   All Rights Reserved.
#
#     Permission is hereby granted, free of charge, to any person obtaining a
#     copy of this software and associated documentation files (the "Software"),
#     to deal in the Software without restriction, including without limitation
#     the rights to use, copy, modify, merge, publish, distribute, sublicense,
#     and/or sell copies of the Software, and to permit persons to whom the
#     Software is furnished to do so, subject to the following conditions:
#
#     The above copyright notice and this permission notice shall be included
#     in all copies or substantial portions of the Software.
#
#     THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#     OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#     FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
#     BRIAN PAUL BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN
#     AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#     CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


################################################################
################################################################


import os, struct, sys

from PyQt5 import QtCore, QtGui


class GtxFile():
    """
    A class that contains basic info about a not-yet-decoded GXT file.
    Based on Wii U GTX Extractor.
    """
    width, height, padWidth, padHeight, format, dataSize = 0, 0, 0, 0, 0, 0
    data = b''

    def padSize(self):
        """
        Calculates the padded image size.
        """
        self.padWidth = (self.width + 63) & ~63
        self.padHeight = (self.height + 63) & ~63


class Gfx2HeaderStruct(struct.Struct):
    """
    Header struct for Gfx2.
    Based on Wii U GTX Extractor.
    """
    def __init__(self, endianness):
        super().__init__(endianness + '4s7I')
    def loadFrom(self, data, idx):
        (self.magic, self._04, self._08, self._0C,
        self._10, self._14, self._18, self._1C) = self.unpack_from(data, idx)


class BLKHeaderStruct(struct.Struct):
    """
    Header struct fot the BLK sections.
    Based on Wii U GTX Extractor.
    """
    def __init__(self, endianness):
        super().__init__(endianness + '4s7I')
    def loadFrom(self, data, idx):
        (self.magic, self._04, self._08, self._0C,
        self._10, self.sectionSize, self._18, self._1C) = self.unpack_from(data, idx)


class RawTexInfoStruct(struct.Struct):
    """
    Struct for raw tex info.
    Based on Wii U GTX Extractor.
    """
    def __init__(self, endianness):
        super().__init__(endianness + '39I')
    def loadFrom(self, data, idx):
        (self._0, self.width, self.height, self._C,
        self._10, self.format_, self._18, self._1C,
        self.sizeMaybe, self._24, self._28, self._2C,
        self._30, self._34, self._38, self._3C,
        self._40, self._44, self._48, self._4C,
        self._50, self._54, self._58, self._5C,
        self._60, self._64, self._68, self._6C,
        self._70, self._74, self._78, self._7C,
        self._80, self._84, self._88, self._8C,
        self._90, self._94, self._98) = self.unpack_from(data, idx)


def loadGTX(input, endianness='>'):
    """
    Takes in data for a GTX image and returns a GtxFile object.
    Based on Wii U GTX Extractor.
    """
    idx = 0
    width, height, format = 0, 0, 0
    gtxData = b''

    # Parse the Gfx2 Header
    headStruct = Gfx2HeaderStruct(endianness)
    headStruct.loadFrom(input, idx)
    if headStruct.magic != b'Gfx2':
        raise ValueError('Wrong file magic!')
    idx += headStruct.size

    # Parse each BLK section
    blkStruct = BLKHeaderStruct(endianness)
    rawTexInfoStruct = RawTexInfoStruct(endianness)
    while idx < len(input):
        blkStruct.loadFrom(input, idx)

        if blkStruct.magic != b'BLK{':
            raise ValueError('Wrong BLK section magic!')
        idx += blkStruct.size

        if blkStruct._10 == 0x0B:
            # Parse raw texture info
            rawTexInfoStruct.loadFrom(input, idx)
            idx += rawTexInfoStruct.size

            width = rawTexInfoStruct.width
            height = rawTexInfoStruct.height
            format = rawTexInfoStruct.format_

        elif blkStruct._10 == 0x0C and len(gtxData) == 0:
            # Grab raw data
            dataSize = blkStruct.sectionSize
            gtxData = input[idx:idx + dataSize]
            idx += dataSize

        else:
            # Ignore.
            idx += blkStruct.sectionSize

    # Make a GtxFile object and return it.
    file = GtxFile()
    file.width = width
    file.height = height
    file.format = format
    file.dataSize = dataSize
    file.data = gtxData
    file.padSize()
    return file


def renderGTX(gtxObj, noalpha=False):
    """
    Renders a GTX object.
    """
    if gtxObj.format == 0x1A:
        return renderRGBA8(gtxObj, noalpha)
    elif gtxObj.format == 0x33:
        return renderDXT5(gtxObj, noalpha)
    else:
        raise NotImplementedError('Unknown texture format: ' + hex(gtxObj.format))


def renderRGBA8(gtx, noalpha):
    """
    Renders a RGBA8 GTX image to a QImage.
    Based on Wii U GTX Extractor.
    """
    # uint32_t pos, x, y;
    # uint32_t *source, *output;
    pos, x, y = 0, 0, 0
    output = bytearray(gtx.padWidth * gtx.padHeight * 4)

    for y in range(gtx.padHeight):
        for x in range(gtx.padWidth):
            pos = (y & ~15) * gtx.padWidth
            pos ^= (x & 3)
            pos ^= ((x >> 2) & 1) << 3
            pos ^= ((x >> 3) & 1) << 6
            pos ^= ((x >> 3) & 1) << 7
            pos ^= (x & ~0xF) << 4
            pos ^= (y & 1) << 2
            pos ^= ((y >> 1) & 7) << 4
            pos ^= (y & 0x10) << 4
            pos ^= (y & 0x20) << 2

            toPos = (y * gtx.width + x) * 4
            pos *= 4
            output[toPos:toPos + 4] = swapRB(gtx.data[pos:pos + 4], noalpha)

    img = QtGui.QImage(output, gtx.padWidth, gtx.padHeight, QtGui.QImage.Format_ARGB32)
    yield img.copy(0, 0, gtx.width, gtx.height)


def swapRB(bgra, noalpha):
    """
    Swaps R and B.
    Based on Wii U GTX Extractor.
    """
    return bytes((bgra[2], bgra[1], bgra[0], 255 if noalpha else bgra[3]))


def renderDXT5(gtx, noalpha):
    """
    Renders a DXT5 GTX image to a QImage.
    Based on Wii U GTX Extractor.
    """
    idx, x, y = 0, 0, 0
    outValue = 0
    blobWidth = gtx.padWidth // 4
    blobHeight = gtx.padHeight // 4
    work = bytearray(gtx.padWidth * gtx.padHeight)

    for y in range(blobHeight):
        for x in range(blobWidth):
            pos = ((y >> 4) * (blobWidth * 16)) & 0xFFFF
            pos ^= (y & 1)
            pos ^= (x & 7) << 1
            pos ^= (x & 8) << 1
            pos ^= (x & 8) << 2
            pos ^= (x & 0x10) << 2
            pos ^= (x & ~0x1F) << 4
            pos ^= (y & 2) << 6
            pos ^= (y & 4) << 6
            pos ^= (y & 8) << 1
            pos ^= (y & 0x10) << 2
            pos ^= (y & 0x20)

            toPos = (y * blobWidth + x) * 16
            pos *= 16
            work[toPos:toPos + 16] = gtx.data[pos:pos + 16]

    output = bytearray(gtx.padWidth * gtx.padHeight * 4)

    for y in range(gtx.padHeight):
        for x in range(gtx.padWidth):
            outValue = calculateRGBAFromDxt5AtPosition(gtx.padWidth, work, x, y, noalpha)

            outputPos = (y * gtx.padWidth + x) * 4
            output[outputPos:outputPos + 4] = outValue

    img = QtGui.QImage(output, gtx.padWidth, gtx.padHeight, QtGui.QImage.Format_ARGB32)
    yield img.copy(0, 0, gtx.width, gtx.height)


def calculateRGBAFromDxt5AtPosition(width, pixdata, i, j, noalpha):
    """
    Fetches a RGBA texel from position (i, j) in a DXT5 texture.
    Based on libtxc_dxtn.
    """
    pointer = ((width + 3) // 4 * (j // 4) + (i // 4)) * 16
    alpha0 = pixdata[pointer]
    alpha1 = pixdata[pointer + 1]

    bit_pos = ((j & 3) * 4 + (i & 3)) * 3
    acodelow = pixdata[pointer + 2 + bit_pos // 8]
    acodehigh = pixdata[pointer + 3 + bit_pos // 8]
    code = (acodelow >> (bit_pos & 0x07) |
        (acodehigh << (8 - (bit_pos & 0x07)))) & 0x07

    a, r, g, b = calculateRGBFromDxtAtPosition(pixdata, pointer + 8, i & 3, j & 3, 2)

    if code == 0:
        a = alpha0
    elif code == 1:
        a = alpha1
    elif alpha0 > alpha1:
        a = (alpha0 * (8 - code) + (alpha1 * (code - 1))) // 7
    elif code < 6:
        a = (alpha0 * (6 - code) + (alpha1 * (code - 1))) // 5
    elif code == 6:
        a = 0
    else:
        a = 255

    return bytes([b, g, r, 255 if noalpha else a])


def calculateRGBFromDxtAtPosition(pixdata, pointer, i, j, dxt_type):
    """
    Fetches a RGB texel from position (i, j) in a DXT1, DXT3 or DXT5 texture.
    Based on libtxc_dxtn.
    """
    color0 = pixdata[pointer] | (pixdata[pointer + 1] << 8)
    color1 = pixdata[pointer + 2] | (pixdata[pointer + 3] << 8)
    bits = (pixdata[pointer + 4] | (pixdata[pointer + 5] << 8) |
        (pixdata[pointer + 6] << 16) | (pixdata[pointer + 7] << 24))

    bit_pos = 2 * (j * 4 + i)
    code = (bits >> bit_pos) & 3

    a = 255

    # Expand r0, b0, r1 and g1 from 5 to 8 bits, and g0 and g1 from 6 to 8 bits.
    r0Expanded = int((color0 >> 11) * 0xFF / 0x1F)
    g0Expanded = int(((color0 >> 5) & 0x3F) * 0xFF / 0x3F)
    b0Expanded = int((color0 & 0x1F) * 0xFF / 0x1F)
    r1Expanded = int((color1 >> 11) * 0xFF / 0x1F)
    g1Expanded = int(((color1 >> 5) & 0x3F) * 0xFF / 0x3F)
    b1Expanded = int((color1 & 0x1F) * 0xFF / 0x1F)

    if code == 0:
        r = r0Expanded
        g = g0Expanded
        b = b0Expanded
    elif code == 1:
        r = r1Expanded
        g = g1Expanded
        b = b1Expanded
    elif code == 2:
        if (dxt_type > 1) or (color0 > color1):
            r = (r0Expanded * 2 + r1Expanded) // 3
            g = (g0Expanded * 2 + g1Expanded) // 3
            b = (b0Expanded * 2 + b1Expanded) // 3
        else:
            r = (r0Expanded + r1Expanded) // 2
            g = (g0Expanded + g1Expanded) // 2
            b = (b0Expanded + b1Expanded) // 2
    elif code == 3:
        if (dxt_type > 1) or (color0 > color1):
            r = (r0Expanded + r1Expanded * 2) // 3
            g = (g0Expanded + g1Expanded * 2) // 3
            b = (b0Expanded + b1Expanded * 2) // 3
        else:
            r, g, b = 0, 0, 0
            if dxt_type == 1: a = 0
    return a, r, g, b


def main():
    """
    This script allows you to run this module as a standalone Python program.
    """
    app = QtCore.QCoreApplication([])

    if len(sys.argv) != 2:
        print("Usage: gtx_extract.py input.gtx")
        sys.exit(1)
    
    with open(sys.argv[1], "rb") as inf:
        print('Converting: '+sys.argv[1])
        inb = inf.read()

    name = os.path.splitext(sys.argv[1])[0]
    for img in renderGTX(loadGTX(inb)):
        img.save(name + ".png")
        print('')
        print('Finished converting: '+sys.argv[1])

if __name__ == '__main__': main()
