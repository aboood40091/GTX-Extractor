#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright © 2016-2017 Stella/AboodXD

# Supported formats:
#  -RGBA8
#  -RGB10A2
#  -RGB565
#  -RGB5A1
#  -RGBA4
#  -L8
#  -L8A8
#  -L4A4
#  -ETC1
#  -BC1
#  -BC2
#  -BC3
#  -BC4U
#  -BC4S
#  -BC5U
#  -BC5S

# Feel free to include this in your own program if you want, just give credits. :)

"""dds.py: DDS reader and header generator."""

import struct, sys, time

def readDDS(f, SRGB):
    with open(f, "rb") as inf:
        inb = inf.read()

    if len(inb) < 0x80 or inb[:4] != b'DDS ':
        print("")
        print("Input is not a valid DDS file!")
        print("")
        print("Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    width = struct.unpack("<I", inb[16:20])[0]
    height = struct.unpack("<I", inb[12:16])[0]

    fourcc = inb[84:88]

    if fourcc == b'DX10':
        print("")
        print("DX10 DDS files are not supported.")
        print("")
        print("Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    pflags = struct.unpack("<I", inb[80:84])[0]
    bpp = struct.unpack("<I", inb[88:92])[0] >> 3
    channel0 = struct.unpack("<I", inb[92:96])[0]
    channel1 = struct.unpack("<I", inb[96:100])[0]
    channel2 = struct.unpack("<I", inb[100:104])[0]
    channel3 = struct.unpack("<I", inb[104:108])[0]
    caps = struct.unpack("<I", inb[108:112])[0]

    if caps not in [0x1000, 0x401008]:
        print("")
        print("Invalid texture.")
        print("")
        print("Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    rgba8_masks = [0xff, 0xff00, 0xff0000, 0xff000000, 0]
    rgb10a2_masks = [0x3ff, 0xffc00, 0x3ff00000, 0xc0000000]
    rgb565_masks = [0xf800, 0x7e0, 0x1f, 0]
    rgb5a1_masks = [0x7c00, 0x3e0, 0x1f, 0x8000]
    rgba4_masks = [0xf00, 0xf0, 0xf, 0xf000]
    l8_masks = [0xff, 0]
    l8a8_masks = [0xff, 0xff00]
    l4a4_masks = [0xf, 0xf0]

    compressed = False
    luminance = False
    rgb = False
    has_alpha = False

    if pflags == 4:
        compressed = True

    elif pflags == 0x20000 or pflags == 2:
        luminance = True

    elif pflags == 0x20001:
        luminance = True
        has_alpha = True

    elif pflags == 0x40:
        rgb = True

    elif pflags == 0x41:
        rgb = True
        has_alpha = True

    format_ = 0

    if compressed:
        compSel = [0, 1, 2, 3]

        if fourcc == b'ETC1':
            format_ = 0x31
            bpp = 8

        elif fourcc == b'DXT1':
            format_ = 0x431 if SRGB else 0x31
            bpp = 8

        elif fourcc == b'DXT3':
            format_ = 0x432 if SRGB else 0x32
            bpp = 16

        elif fourcc == b'DXT5':
            format_ = 0x433 if SRGB else 0x33
            bpp = 16

        elif fourcc in [b'BC4U', b'ATI1']:
            format_ = 0x34
            bpp = 8

        elif fourcc == b'BC4S':
            format_ = 0x234
            bpp = 8

        elif fourcc in [b'BC5U', b'ATI2']:
            format_ = 0x35
            bpp = 16

        elif fourcc == b'BC4S':
            format_ = 0x235
            bpp = 16

        size = ((width + 3) // 4) * ((height + 3) // 4) * bpp

    else:
        compSel = []

        if luminance:
            if has_alpha:
                if channel0 in l8a8_masks and channel1 in l8a8_masks and channel2 in l8a8_masks and channel3 in l8a8_masks and bpp == 2:
                    format_ = 7

                    if channel0 == 0xff:
                        compSel.append(0)
                    elif channel0 == 0xff00:
                        compSel.append(3)

                    if channel1 == 0xff:
                        compSel.append(0)
                    elif channel1 == 0xff00:
                        compSel.append(3)

                    if channel2 == 0xff:
                        compSel.append(0)
                    elif channel2 == 0xff00:
                        compSel.append(3)

                    if channel3 == 0xff:
                        compSel.append(0)
                    elif channel3 == 0xff00:
                        compSel.append(3)
                        

                elif channel0 in l4a4_masks and channel1 in l4a4_masks and channel2 in l4a4_masks and channel3 in l4a4_masks and bpp == 1:
                    format_ = 2

                    if channel0 == 0xf:
                        compSel.append(0)
                    elif channel0 == 0xf0:
                        compSel.append(3)

                    if channel1 == 0xf:
                        compSel.append(0)
                    elif channel1 == 0xf0:
                        compSel.append(3)

                    if channel2 == 0xf:
                        compSel.append(0)
                    elif channel2 == 0xf0:
                        compSel.append(3)

                    if channel3 == 0xf:
                        compSel.append(0)
                    elif channel3 == 0xf0:
                        compSel.append(3)

            else:
                if channel0 in l8_masks and channel1 in l8_masks and channel2 in l8_masks and channel3 in l8_masks and bpp == 1:
                    format_ = 1

                    if channel0 == 0xff:
                        compSel.append(3 if pflags == 2 else 0)
                    elif channel0 == 0:
                        compSel.append(4)

                    if channel1 == 0xff:
                        compSel.append(3 if pflags == 2 else 0)
                    elif channel1 == 0:
                        compSel.append(4)

                    if channel2 == 0xff:
                        compSel.append(3 if pflags == 2 else 0)
                    elif channel2 == 0:
                        compSel.append(4)

                    if channel3 == 0xff:
                        compSel.append(3 if pflags == 2 else 0)
                    elif channel3 == 0:
                        compSel.append(4)
        elif rgb:
            if has_alpha:
                if bpp == 4:
                    if channel0 in rgba8_masks and channel1 in rgba8_masks and channel2 in rgba8_masks and channel3 in rgba8_masks:
                        format_ = 0x41a if SRGB else 0x1a

                        if channel0 == 0xff:
                            compSel.append(0)
                        elif channel0 == 0xff00:
                            compSel.append(1)
                        elif channel0 == 0xff0000:
                            compSel.append(2)
                        elif channel0 == 0xff000000:
                            compSel.append(3)
                        elif channel0 == 0:
                            compSel.append(4)

                        if channel1 == 0xff:
                            compSel.append(0)
                        elif channel1 == 0xff00:
                            compSel.append(1)
                        elif channel1 == 0xff0000:
                            compSel.append(2)
                        elif channel1 == 0xff000000:
                            compSel.append(3)
                        elif channel1 == 0:
                            compSel.append(4)

                        if channel2 == 0xff:
                            compSel.append(0)
                        elif channel2 == 0xff00:
                            compSel.append(1)
                        elif channel2 == 0xff0000:
                            compSel.append(2)
                        elif channel2 == 0xff000000:
                            compSel.append(3)
                        elif channel2 == 0:
                            compSel.append(4)

                        if channel3 == 0xff:
                            compSel.append(0)
                        elif channel3 == 0xff00:
                            compSel.append(1)
                        elif channel3 == 0xff0000:
                            compSel.append(2)
                        elif channel3 == 0xff000000:
                            compSel.append(3)
                        elif channel3 == 0:
                            compSel.append(4)

                    elif channel0 in rgb10a2_masks and channel1 in rgb10a2_masks and channel2 in rgb10a2_masks and channel3 in rgb10a2_masks:
                        format_ = 0x19

                        if channel0 == 0x3ff:
                            compSel.append(0)
                        elif channel0 == 0xffc00:
                            compSel.append(1)
                        elif channel0 == 0x3ff00000:
                            compSel.append(2)
                        elif channel0 == 0xc0000000:
                            compSel.append(3)

                        if channel1 == 0x3ff:
                            compSel.append(0)
                        elif channel1 == 0xffc00:
                            compSel.append(1)
                        elif channel1 == 0x3ff00000:
                            compSel.append(2)
                        elif channel1 == 0xc0000000:
                            compSel.append(3)

                        if channel2 == 0x3ff:
                            compSel.append(0)
                        elif channel2 == 0xffc00:
                            compSel.append(1)
                        elif channel2 == 0x3ff00000:
                            compSel.append(2)
                        elif channel2 == 0xc0000000:
                            compSel.append(3)

                        if channel3 == 0x3ff:
                            compSel.append(0)
                        elif channel3 == 0xffc00:
                            compSel.append(1)
                        elif channel3 == 0x3ff00000:
                            compSel.append(2)
                        elif channel3 == 0xc0000000:
                            compSel.append(3)

                elif bpp == 2:
                    if channel0 in rgb5a1_masks and channel1 in rgb5a1_masks and channel2 in rgb5a1_masks and channel3 in rgb5a1_masks:
                        format_ = 0xa

                        if channel0 == 0x1f:
                            compSel.append(2)
                        elif channel0 == 0x3e0:
                            compSel.append(1)
                        elif channel0 == 0x7c00:
                            compSel.append(0)
                        elif channel0 == 0x8000:
                            compSel.append(3)

                        if channel1 == 0x1f:
                            compSel.append(2)
                        elif channel1 == 0x3e0:
                            compSel.append(1)
                        elif channel1 == 0x7c00:
                            compSel.append(0)
                        elif channel1 == 0x8000:
                            compSel.append(3)

                        if channel2 == 0x1f:
                            compSel.append(2)
                        elif channel2 == 0x3e0:
                            compSel.append(1)
                        elif channel2 == 0x7c00:
                            compSel.append(0)
                        elif channel2 == 0x8000:
                            compSel.append(3)

                        if channel3 == 0x1f:
                            compSel.append(2)
                        elif channel3 == 0x3e0:
                            compSel.append(1)
                        elif channel3 == 0x7c00:
                            compSel.append(0)
                        elif channel3 == 0x8000:
                            compSel.append(3)

                    elif channel0 in rgba4_masks and channel1 in rgba4_masks and channel2 in rgba4_masks and channel3 in rgba4_masks:
                        format_ = 0xb

                        if channel0 == 0xf:
                            compSel.append(2)
                        elif channel0 == 0xf0:
                            compSel.append(1)
                        elif channel0 == 0xf00:
                            compSel.append(0)
                        elif channel0 == 0xf000:
                            compSel.append(3)

                        if channel1 == 0xf:
                            compSel.append(2)
                        elif channel1 == 0xf0:
                            compSel.append(1)
                        elif channel1 == 0xf00:
                            compSel.append(0)
                        elif channel1 == 0xf000:
                            compSel.append(3)

                        if channel2 == 0xf:
                            compSel.append(2)
                        elif channel2 == 0xf0:
                            compSel.append(1)
                        elif channel2 == 0xf00:
                            compSel.append(0)
                        elif channel2 == 0xf000:
                            compSel.append(3)

                        if channel3 == 0xf:
                            compSel.append(2)
                        elif channel3 == 0xf0:
                            compSel.append(1)
                        elif channel3 == 0xf00:
                            compSel.append(0)
                        elif channel3 == 0xf000:
                            compSel.append(3)

            else:
                if channel0 in rgba8_masks and channel1 in rgba8_masks and channel2 in rgba8_masks and channel3 in rgba8_masks and bpp == 3:
                    format_ = 0x41a if SRGB else 0x1a

                    if channel0 == 0xff:
                        compSel.append(0)
                    elif channel0 == 0xff00:
                        compSel.append(1)
                    elif channel0 == 0xff0000:
                        compSel.append(2)
                    elif channel0 == 0xff000000:
                        compSel.append(3)
                    elif channel0 == 0:
                        compSel.append(4)

                    if channel1 == 0xff:
                        compSel.append(0)
                    elif channel1 == 0xff00:
                        compSel.append(1)
                    elif channel1 == 0xff0000:
                        compSel.append(2)
                    elif channel1 == 0xff000000:
                        compSel.append(3)
                    elif channel1 == 0:
                        compSel.append(4)

                    if channel2 == 0xff:
                        compSel.append(0)
                    elif channel2 == 0xff00:
                        compSel.append(1)
                    elif channel2 == 0xff0000:
                        compSel.append(2)
                    elif channel2 == 0xff000000:
                        compSel.append(3)
                    elif channel2 == 0:
                        compSel.append(4)

                    if channel3 == 0xff:
                        compSel.append(0)
                    elif channel3 == 0xff00:
                        compSel.append(1)
                    elif channel3 == 0xff0000:
                        compSel.append(2)
                    elif channel3 == 0xff000000:
                        compSel.append(3)
                    elif channel3 == 0:
                        compSel.append(4)

                if channel0 in rgb565_masks and channel1 in rgb565_masks and channel2 in rgb565_masks and channel3 in rgb565_masks and bpp == 2:
                    format_ = 8

                    if channel0 == 0x1f:
                        compSel.append(2)
                    elif channel0 == 0x7e0:
                        compSel.append(1)
                    elif channel0 == 0xf800:
                        compSel.append(0)
                    elif channel0 == 0:
                        compSel.append(4)

                    if channel1 == 0x1f:
                        compSel.append(2)
                    elif channel1 == 0x7e0:
                        compSel.append(1)
                    elif channel1 == 0xf800:
                        compSel.append(0)
                    elif channel1 == 0:
                        compSel.append(4)

                    if channel2 == 0x1f:
                        compSel.append(2)
                    elif channel2 == 0x7e0:
                        compSel.append(1)
                    elif channel2 == 0xf800:
                        compSel.append(0)
                    elif channel2 == 0:
                        compSel.append(4)

                    if channel3 == 0x1f:
                        compSel.append(2)
                    elif channel3 == 0x7e0:
                        compSel.append(1)
                    elif channel3 == 0xf800:
                        compSel.append(0)
                    elif channel3 == 0:
                        compSel.append(4)

        size = width * height * bpp

    if len(inb) < 0x80+size:
        print("")
        print("Input is not a valid DDS file!")
        print("")
        print("Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    if format_ == 0:
        print("")
        print("Unsupported DDS format!")
        print("")
        print("Exiting in 5 seconds...")
        time.sleep(5)
        sys.exit(1)

    data = inb[0x80:0x80+size]

    # insert "RGB8 to RGBA8" here

    return width, height, format_, fourcc, size, compSel, data


def generateHeader(num_mipmaps, w, h, format_, compSel, size, compressed):
    hdr = bytearray(128)

    if format_ == 28:  # RGBA8
        fmtbpp = 4
        has_alpha = 1
        rmask = 0x000000ff
        gmask = 0x0000ff00
        bmask = 0x00ff0000
        amask = 0xff000000

    elif format_ == 24:  # RGB10A2
        fmtbpp = 4
        has_alpha = 1
        rmask = 0x000003ff
        gmask = 0x000ffc00
        bmask = 0x3ff00000
        amask = 0xc0000000

    elif format_ == 85:  # RGB565
        fmtbpp = 2
        has_alpha = 0
        rmask = 0x0000f800
        gmask = 0x000007e0
        bmask = 0x0000001f
        amask = 0x00000000

    elif format_ == 86:  # RGB5A1
        fmtbpp = 2
        has_alpha = 1
        rmask = 0x00007c00
        gmask = 0x000003e0
        bmask = 0x0000001f
        amask = 0x00008000

    elif format_ == 115:  # RGBA4
        fmtbpp = 2
        has_alpha = 1
        rmask = 0x00000f00
        gmask = 0x000000f0
        bmask = 0x0000000f
        amask = 0x0000f000

    elif format_ == 61:  # L8
        fmtbpp = 1
        has_alpha = 0
        rmask = 0x000000ff
        gmask = 0x000000ff
        bmask = 0x000000ff
        amask = 0x00000000
        if compSel.count(3) == 1:
            has_alpha = 1
            amask = 0x000000ff

    elif format_ == 49:  # L8A8
        fmtbpp = 2
        has_alpha = 1
        rmask = 0x000000ff
        gmask = 0x000000ff
        bmask = 0x000000ff
        amask = 0x0000ff00

    elif format_ == 112:  # L4A4
        fmtbpp = 1
        has_alpha = 1
        rmask = 0x0000000f
        gmask = 0x0000000f
        bmask = 0x0000000f
        amask = 0x000000f0

    flags = 0x00000001 | 0x00001000 | 0x00000004 | 0x00000002

    caps = 0x00001000

    if num_mipmaps == 0:
        num_mipmaps = 1
    elif num_mipmaps != 1:
        flags |= 0x00020000
        caps |= 0x00000008 | 0x00400000

    if not compressed:
        flags |= 0x00000008

        if (fmtbpp == 1 and not has_alpha) or format_ == 49:  # LUMINANCE
            pflags = 0x00020000

        elif fmtbpp == 1 and has_alpha:
            pflags = 0x00000002

        else:  # RGB
            pflags = 0x00000040

        if has_alpha and fmtbpp != 1:
            pflags |= 0x00000001

        size = w * fmtbpp

    else:
        flags |= 0x00080000
        pflags = 0x00000004

        if format_ == "ETC1":
            fourcc = b'ETC1'
        elif format_ == "BC1":
            fourcc = b'DXT1'
        elif format_ == "BC2":
            fourcc = b'DXT3'
        elif format_ == "BC3":
            fourcc = b'DXT5'
        elif format_ == "BC4U":
            fourcc = b'ATI1'
        elif format_ == "BC4S":
            fourcc = b'BC4S'
        elif format_ == "BC5U":
            fourcc = b'ATI2'
        elif format_ == "BC5S":
            fourcc = b'BC5S'

    hdr[:4] = b'DDS '
    hdr[4:4 + 4] = 124 .to_bytes(4, 'little')
    hdr[8:8 + 4] = flags.to_bytes(4, 'little')
    hdr[12:12 + 4] = h.to_bytes(4, 'little')
    hdr[16:16 + 4] = w.to_bytes(4, 'little')
    hdr[20:20 + 4] = size.to_bytes(4, 'little')
    hdr[28:28 + 4] = num_mipmaps.to_bytes(4, 'little')
    hdr[76:76 + 4] = 32 .to_bytes(4, 'little')
    hdr[80:80 + 4] = pflags.to_bytes(4, 'little')

    if compressed:
        hdr[84:84 + 4] = fourcc
    else:
        hdr[88:88 + 4] = (fmtbpp << 3).to_bytes(4, 'little')

        if compSel[0] == 1:
            hdr[92:92 + 4] = gmask.to_bytes(4, 'little')
        elif compSel[0] == 2:
            hdr[92:92 + 4] = bmask.to_bytes(4, 'little')
        elif compSel[0] == 3:
            hdr[92:92 + 4] = amask.to_bytes(4, 'little')
        elif compSel[0] == 4:
            hdr[92:92 + 4] = 0 .to_bytes(4, 'little')
        else:
            hdr[92:92 + 4] = rmask.to_bytes(4, 'little')

        if compSel[1] == 0:
            hdr[96:96 + 4] = rmask.to_bytes(4, 'little')
        elif compSel[1] == 2:
            hdr[96:96 + 4] = bmask.to_bytes(4, 'little')
        elif compSel[1] == 3:
            hdr[96:96 + 4] = amask.to_bytes(4, 'little')
        elif compSel[1] == 4:
            hdr[96:96 + 4] = 0 .to_bytes(4, 'little')
        else:
            hdr[96:96 + 4] = gmask.to_bytes(4, 'little')

        if compSel[2] == 0:
            hdr[100:100 + 4] = rmask.to_bytes(4, 'little')
        elif compSel[2] == 1:
            hdr[100:100 + 4] = gmask.to_bytes(4, 'little')
        elif compSel[2] == 3:
            hdr[100:100 + 4] = amask.to_bytes(4, 'little')
        elif compSel[2] == 4:
            hdr[100:100 + 4] = 0 .to_bytes(4, 'little')
        else:
            hdr[100:100 + 4] = bmask.to_bytes(4, 'little')

        if compSel[3] == 0:
            hdr[104:104 + 4] = rmask.to_bytes(4, 'little')
        elif compSel[3] == 1:
            hdr[104:104 + 4] = gmask.to_bytes(4, 'little')
        elif compSel[3] == 2:
            hdr[104:104 + 4] = bmask.to_bytes(4, 'little')
        elif compSel[3] == 4:
            hdr[104:104 + 4] = 0 .to_bytes(4, 'little')
        else:
            hdr[104:104 + 4] = amask.to_bytes(4, 'little')

    hdr[108:108 + 4] = caps.to_bytes(4, 'little')

    return hdr
