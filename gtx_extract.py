#!/usr/bin/env python

"""gtx_extract.py: Decode GTX images."""

import os, struct, sys

from PyQt5 import QtCore, QtGui

__author__ = "AboodXD"
__copyright__ = "Copyright 2016, AboodXD"
__credits__ = ["AboodXD", "libdxtn", "Treeki",
                    "Reggie Next! team"]

# ----------\/-Start of libdxtn section-\/---------- #
def Expand_shit(packedcol):
    EXP5TO8R = int((((packedcol) >> 8) & 0xf8) | (((packedcol) >> 13) & 0x07))
    EXP6TO8G = int((((packedcol) >> 3) & 0xfc) | (((packedcol) >>  9) & 0x03))
    EXP5TO8B = int((((packedcol) << 3) & 0xf8) | (((packedcol) >>  2) & 0x07))

    return EXP5TO8R, EXP6TO8G, EXP5TO8B

def dxt135_decode_imageblock(pixdata, img_block_src, i, j, dxt_type):
    color0 = pixdata[img_block_src] | (pixdata[img_block_src + 1] << 8)
    color1 = pixdata[img_block_src + 2] | (pixdata[img_block_src + 3] << 8)
    bits = (pixdata[img_block_src + 4] | (pixdata[img_block_src + 5] << 8) |
        (pixdata[img_block_src + 6] << 16) | (pixdata[img_block_src + 7] << 24))
    # What about big/little endian?
    bit_pos = 2 * (j * 4 + i)
    code = (bits >> bit_pos) & 3

    ACOMP = 255

    EXP5TO8R0, EXP6TO8G0, EXP5TO8B0 = Expand_shit(color0)
    EXP5TO8R1, EXP6TO8G1, EXP5TO8B1 = Expand_shit(color1)

    if code == 0:
        RCOMP = EXP5TO8R0
        GCOMP = EXP6TO8G0
        BCOMP = EXP5TO8B0
    elif code == 1:
        RCOMP = EXP5TO8R1
        GCOMP = EXP6TO8G1
        BCOMP = EXP5TO8B1
    elif code == 2:
        if (dxt_type > 1) or (color0 > color1):
            RCOMP = (EXP5TO8R0 * 2 + EXP5TO8R1) // 3
            GCOMP = (EXP6TO8G0 * 2 + EXP6TO8G1) // 3
            BCOMP = (EXP5TO8B0 * 2 + EXP5TO8B1) // 3
        else:
            RCOMP = (EXP5TO8R0 + EXP5TO8R1) // 2
            GCOMP = (EXP6TO8G0 + EXP6TO8G1) // 2
            BCOMP = (EXP5TO8B0 + EXP5TO8B1) // 2
    elif code == 3:
        if (dxt_type > 1) or (color0 > color1):
            RCOMP = (EXP5TO8R0 + EXP5TO8R1 * 2) // 3
            GCOMP = (EXP6TO8G0 + EXP6TO8G1 * 2) // 3
            BCOMP = (EXP5TO8B0 + EXP5TO8B1 * 2) // 3
        else:
            RCOMP = 0
            GCOMP = 0
            BCOMP = 0
            if dxt_type == 1: ACOMP = 0
    return ACOMP, RCOMP, GCOMP, BCOMP

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

    return bytes([BCOMP, GCOMP, RCOMP, ACOMP]) # Best way to swap R and B, nice! :)
    
# ----------\/-Start of GTX Extractor section-\/------------- #
class GTXData():
    width, height = 0, 0
    format = 0
    dataSize = 0
    data = b''

class GTXRawHeader(struct.Struct):
    def __init__(self):
        super().__init__('>4s7I') # Totally stolen, thanks Reggie Next team!

    def data(self, data, idx):
        (self.magic,
        self._04, self._08, self._0C, self._10, self._14, self._18, self._1C) = self.unpack_from(data, idx)

class GTXRawSectionHeader(struct.Struct):
    def __init__(self):
        super().__init__('>4s7I') # Totally stolen, thanks Reggie Next team!

    def data(self, data, idx):
        (self.magic,
        self._04, self._08, self._0C, self._10,
        self.size_,
        self._18, self._1C) = self.unpack_from(data, idx)

class GTXRawTextureInfo(struct.Struct):
    def __init__(self):
        super().__init__('>39I') # Totally stolen, thanks Reggie Next team!

    def data(self, data, idx):
        (self._00, self.width, self.height, self._0C,
        self._10, self.formatMaybe, self._18, self._1C,
        self.sizeMaybe, self._24, self._28, self._2C,
        self._30, self._34, self._38, self._3C,
        self._40, self._44, self._48, self._4C,
        self._50, self._54, self._58, self._5C,
        self._60, self._64, self._68, self._6C,
        self._70, self._74, self._78, self._7C,
        self._80, self._84, self._88, self._8C,
        self._90, self._94, self._98) = self.unpack_from(data, idx)

def swapRB(argb):

    """
    Swaps R and B.
    Don't ask me why, it's based of Treeki's GTX Extractor.
    """

    return bytes((argb[2], argb[1], argb[0], argb[3])) # 0 is R, 1 is G, 2 is B, and 3 is A. 0 and 2 must be swapped!


def readGTX(f, gtx = GTXData):
    idx = 0

    header = GTXRawHeader()

    # This is kinda bad. Don't really care right now >.>
    gtx.width = 0
    gtx.height = 0
    gtx.data = b''

    header.data(f, idx)
    
    if header.magic != b'Gfx2':
        sys.exit("Invalid file magic!")

    idx += header.size

    while idx < len(f):
        section = GTXRawSectionHeader()
        section.data(f, idx)

        if section.magic != b'BLK{':
            sys.exit("Invalid section magic!")

        idx += section.size

        if section._10 == 0x0B:
            info = GTXRawTextureInfo()
            info.data(f, idx)

            idx += info.size

            if section.size_ != 0x9C :
                sys.exit("Invalid section size!")

            gtx.width = info.width
            gtx.height = info.height
            gtx.format = info.formatMaybe

        elif section._10 == 0x0C and len(gtx.data) == 0:
            gtx.dataSize = section.size_
            gtx.data = f[idx:idx + gtx.dataSize]
            idx += gtx.dataSize

        else:
            idx += section.size_

    return gtx

def writeFile(data):
    if data.format == 0x1A:
        return export_RGBA8(data)
    elif data.format == 0x33:
        return export_DXT5(data)
    else:
        raise NotImplementedError('Unimplemented texture format: ' + hex(data.format))

def export_RGBA8(gtx):
    pos, x, y = 0, 0, 0

    source = gtx.data
    output = bytearray(gtx.width * gtx.height * 4)

    for y in range(gtx.height):
        for x in range(gtx.width):
            pos = (y & ~15) * gtx.width
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

    img = QtGui.QImage(output, gtx.width, gtx.height, QtGui.QImage.Format_ARGB32)
    yield img.copy(0, 0, gtx.width, gtx.height)

def export_DXT5(gtx):
    idx, x, y = 0, 0, 0
    outValue = 0
    blobWidth = gtx.width // 4
    blobHeight = gtx.height // 4
    work = bytearray(gtx.width * gtx.height)

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

    output = bytearray(gtx.width * gtx.height * 4)

    for y in range(gtx.height):
        for x in range(gtx.width):
            outValue = fetch_2d_texel_rgba_dxt5(gtx.width, work, x, y)

            outputPos = (y * gtx.width + x) * 4
            output[outputPos:outputPos + 4] = outValue

    img = QtGui.QImage(output, gtx.width, gtx.height, QtGui.QImage.Format_ARGB32)
    yield img.copy(0, 0, gtx.width, gtx.height)


def main():
    """
    This script allows you to run this module as a standalone Python program.
    Also, this place is a mess...
    """
    app = QtCore.QCoreApplication([])

    if len(sys.argv) != 2:
        print("Usage: gtx_extract.py input.gtx")
        sys.exit(1)
    
    with open(sys.argv[1], "rb") as inf:
        print('Converting: '+sys.argv[1])
        inb = inf.read()

    data = readGTX(inb)

    print('')
    print("Width: " + str(data.width) + " - Height: " + str(data.height) + " - Format: " + hex(data.format) + " - Size: " + str(data.dataSize))

    data.width = (data.width + 63) & ~63
    data.height = (data.height + 63) & ~63
    print("Padded Width: " + str(data.width) + " - Padded Height: " + str(data.height))

    name = os.path.splitext(sys.argv[1])[0]

    for img in writeFile(data):
        img.save(name + ".png")
        print('')
        print('Finished converting: '+sys.argv[1])

if __name__ == '__main__': main()
