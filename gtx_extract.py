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

    return bytes([RCOMP, GCOMP, BCOMP, ACOMP])
    
# ----------\/-Start of GTX Extractor section-\/------------- #
class GTXData():
    width, height = 0, 0
    format = 0
    dataSize = 0
    data = b''

class GFDHeader(struct.Struct):
    def __init__(self):
        super().__init__('>4s7I') # Totally stolen, thanks Reggie Next team!

    def data(self, data, pos):
        (self.magic,
        self.size, self.majorVersion, self.minorVersion, self.gpuVersion, self.alignMode, self.reserved1, self.reserved2) = self.unpack_from(data, pos)

class GFDBlockHeader(struct.Struct):
    def __init__(self):
        super().__init__('>4s7I') # Totally stolen, thanks Reggie Next team!

    def data(self, data, pos):
        (self.magic,
        self.size, self.majorVersion, self.minorVersion, self.type,
        self.dataSize,
        self.id, self.typeIdx) = self.unpack_from(data, pos)

class GFDSurface(struct.Struct):
    def __init__(self):
        super().__init__('>39I') # Totally stolen, thanks Reggie Next team!

    def data(self, data, pos):
        (self.dim, self.width, self.height, self.depth,
        self.numMips, self.format, self.aa, self.use,
        self.imageSize, self.imagePtr, self.mipSize, self.mipPtr,
        self.tileMode, self.swizzle, self.alignment, self.pitch,
        self.mipOffset) = self.unpack_from(data, pos)

def readGTX(f):
    gtx = GTXData()
    pos = 0

    header = GFDHeader()

    # This is kinda bad. Don't really care right now >.>
    gtx.width = 0
    gtx.height = 0
    gtx.data = b''

    header.data(f, pos)
    
    if header.magic != b'Gfx2':
        sys.exit("Invalid file magic!")

    pos += header.size

    while pos < len(f):
        section = GFDBlockHeader()
        section.data(f, pos)

        if section.magic != b'BLK{':
            sys.exit("Invalid section magic!")

        pos += section.size

        if section.type == 0x0B:
            info = GFDSurface()
            info.data(f, pos)

            pos += info.size

            if section.dataSize != 0x9C :
                sys.exit("Invalid section size!")

            gtx.width = info.width
            gtx.height = info.height
            gtx.format = info.format

        elif section.type == 0x0C and len(gtx.data) == 0:
            gtx.dataSize = section.dataSize
            gtx.data = f[pos:pos + section.dataSize]
            pos += section.dataSize

        else:
            pos += section.dataSize

    return gtx

def writeFile(data):
    if data.format == 0x1A:
        return export_RGBA8(data)
    elif data.format == 0x33:
        return export_DXT5(data)
    else:
        sys.exit("Unimplemented texture format: " + hex(data.format))

def export_RGBA8(gtx):
    gtx.width_ = (gtx.width + 63) & ~63
    gtx.height_ = (gtx.height + 63) & ~63

    pos, x, y = 0, 0, 0

    source = gtx.data
    output = bytearray(gtx.width_ * gtx.height_ * 4)

    for y in range(gtx.height_):
        for x in range(gtx.width_):
            pos = (y & ~15) * gtx.width_
            pos ^= (x & 3)
            pos ^= ((x >> 2) & 1) << 3
            pos ^= ((x >> 3) & 1) << 6
            pos ^= ((x >> 3) & 1) << 7
            pos ^= (x & ~0xF) << 4
            pos ^= (y & 1) << 2
            pos ^= ((y >> 1) & 7) << 4
            pos ^= (y & 0x10) << 4
            pos ^= (y & 0x20) << 2
            pos_ = (y * gtx.width_ + x) * 4
            pos *= 4
            output[pos_:pos_ + 4] = gtx.data[pos:pos + 4]

    img = QtGui.QImage(output, gtx.width_, gtx.height_, QtGui.QImage.Format_RGBA8888)
    yield img.copy(0, 0, gtx.width, gtx.height)

def export_DXT5(gtx):
    gtx.width_ = (gtx.width + 63) & ~63
    gtx.height_ = (gtx.height + 63) & ~63

    pos, x, y = 0, 0, 0
    outValue = 0
    blobWidth = gtx.width_ // 4
    blobHeight = gtx.height_ // 4
    work = bytearray(gtx.width_ * gtx.height_)

    for y in range(blobHeight):
        for x in range(blobWidth):
            pos = (y >> 4) * (blobWidth * 16)
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

            pos_ = (y * blobWidth + x) * 16
            pos *= 16
            work[pos_:pos_ + 16] = gtx.data[pos:pos + 16]

    output = bytearray(gtx.width_ * gtx.height_ * 4)

    for y in range(gtx.height_):
        for x in range(gtx.width_):
            outValue = fetch_2d_texel_rgba_dxt5(gtx.width_, work, x, y)

            pos__ = (y * gtx.width_ + x) * 4
            output[pos__:pos__ + 4] = outValue

    img = QtGui.QImage(output, gtx.width_, gtx.height_, QtGui.QImage.Format_RGBA8888)
    yield img.copy(0, 0, gtx.width, gtx.height)


def main():
    """
    This place is a mess...
    """
    if len(sys.argv) != 2:
        print("Usage: gtx_extract.py input.gtx")
        sys.exit(1)
    
    with open(sys.argv[1], "rb") as inf:
        print('Converting: ' + sys.argv[1])
        inb = inf.read()
        inf.close()

    data = readGTX(inb)

    print('')
    print("Width: " + str(data.width) + " - Height: " + str(data.height) + " - Format: " + hex(data.format) + " - Size: " + str(data.dataSize))

    data.width_ = (data.width + 63) & ~63
    data.height_ = (data.height + 63) & ~63
    print("Padded Width: " + str(data.width_) + " - Padded Height: " + str(data.height_))

    name = os.path.splitext(sys.argv[1])[0]

    for img in writeFile(data):
        img.save(name + ".png")
        print('')
        print('Finished converting: ' + sys.argv[1])

if __name__ == '__main__': main()
