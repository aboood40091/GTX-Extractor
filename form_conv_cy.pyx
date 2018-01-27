#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright © 2016-2018 AboodXD

################################################################
################################################################

ctypedef unsigned char u8
ctypedef unsigned short u16
ctypedef unsigned int u32


cpdef bytes toGX2rgb5a1(u8[:] data):
    cdef u32 numPixels = len(data) // 2

    cdef bytearray new_data = bytearray(numPixels * 2)

    cdef u32 i
    cdef u16 pixel, new_pixel
    cdef u8 red, green, blue, alpha

    for i in range(numPixels):
        pixel = (data[2 * i] << 8) | data[2 * i + 1]

        red = (pixel >> 10) & 0x1F
        green = (pixel >> 5) & 0x1F
        blue = pixel & 0x1F
        alpha = (pixel >> 15) & 1

        new_pixel = (red << 11) | (green << 6) | (blue << 1) | alpha

        new_data[2 * i + 0] = (new_pixel & 0xFF00) >> 8
        new_data[2 * i + 1] = new_pixel & 0xFF

    return bytes(new_data)


cpdef bytes toDDSrgb5a1(u8[:] data):
    cdef u32 numPixels = len(data) // 2

    cdef bytearray new_data = bytearray(numPixels * 2)

    cdef u32 i
    cdef u16 pixel, new_pixel
    cdef u8 red, green, blue, alpha

    for i in range(numPixels):
        pixel = (data[2 * i] << 8) | data[2 * i + 1]

        red = (pixel >> 11) & 0x1F
        green = (pixel >> 6) & 0x1F
        blue = (pixel >> 1) & 0x1F
        alpha = pixel & 1

        new_pixel = (red << 10) | (green << 5) | blue | (alpha << 15)

        new_data[2 * i + 0] = (new_pixel & 0xFF00) >> 8
        new_data[2 * i + 1] = new_pixel & 0xFF

    return bytes(new_data)


cpdef bytes rgb8torgbx8(u8[:] data):
    cdef u32 numPixels = len(data) // 3

    cdef bytearray new_data = bytearray(numPixels * 4)

    cdef u32 i

    for i in range(numPixels):
        new_data[4 * i + 0] = data[3 * i + 0]
        new_data[4 * i + 1] = data[3 * i + 1]
        new_data[4 * i + 2] = data[3 * i + 2]
        new_data[4 * i + 3] = 0xFF

    return bytes(new_data)


cpdef bytes swapRB_RGB565(u8[:] data):
    cdef u32 numPixels = len(data) // 2

    cdef bytearray new_data = bytearray(numPixels * 2)

    cdef u32 i
    cdef u16 pixel, new_pixel
    cdef u8 red, green, blue

    for i in range(numPixels):
        pixel = (
            data[2 * i + 0] |
            (data[2 * i + 1] << 8)
        )

        red = (pixel >> 11) & 0x1F
        green = (pixel >> 5) & 0x3F
        blue = pixel & 0x1F

        new_pixel = (blue << 11) | (green << 5) | red

        new_data[2 * i + 1] = (new_pixel & 0xFF00) >> 8
        new_data[2 * i + 0] = new_pixel & 0xFF

    return bytes(new_data)


cpdef bytes swapRB_RGB5A1(u8[:] data):
    cdef u32 numPixels = len(data) // 2

    cdef bytearray new_data = bytearray(numPixels * 2)

    cdef u32 i
    cdef u16 pixel, new_pixel
    cdef u8 red, green, blue, alpha

    for i in range(numPixels):
        pixel = (
            data[2 * i + 0] |
            (data[2 * i + 1] << 8)
        )

        red = (pixel >> 10) & 0x1F
        green = (pixel >> 5) & 0x1F
        blue = pixel & 0x1F
        alpha = (pixel >> 15) & 0x1

        new_pixel = (blue << 10) | (green << 5) | red | (alpha << 15)

        new_data[2 * i + 1] = (new_pixel & 0xFF00) >> 8
        new_data[2 * i + 0] = new_pixel & 0xFF

    return bytes(new_data)


cpdef bytes swapRB_RGBA4(u8[:] data):
    cdef u32 numPixels = len(data) // 2

    cdef bytearray new_data = bytearray(numPixels * 2)

    cdef u32 i
    cdef u16 pixel, new_pixel
    cdef u8 red, green, blue, alpha

    for i in range(numPixels):
        pixel = (
            data[2 * i + 0] |
            (data[2 * i + 1] << 8)
        )

        red = (pixel >> 8) & 0xF
        green = (pixel >> 4) & 0xF
        blue = pixel & 0xF
        alpha = (pixel >> 12) & 0xF

        new_pixel = (blue << 8) | (green << 4) | red | (alpha << 12)

        new_data[2 * i + 1] = (new_pixel & 0xFF00) >> 8
        new_data[2 * i + 0] = new_pixel & 0xFF

    return bytes(new_data)


cpdef bytes swapRB_RGB10A2(u8[:] data):
    cdef u32 numPixels = len(data) // 4

    cdef bytearray new_data = bytearray(numPixels * 4)

    cdef u32 i, pixel, new_pixel
    cdef u8 red, green, blue, alpha

    for i in range(numPixels):
        pixel = (
            data[4 * i + 0] |
            (data[4 * i + 1] << 8) |
            (data[4 * i + 2] << 16) |
            (data[4 * i + 3] << 24)
        )

        red = (pixel >> 22) & 0xFF
        green = (pixel >> 12) & 0xFF
        blue = (pixel >> 2) & 0xFF
        alpha = (pixel >> 30) & 0x3

        new_pixel = (blue << 22) | (green << 12) | (red << 2) | (alpha << 30)

        new_data[4 * i + 3] = (new_pixel & 0xFF000000) >> 24
        new_data[4 * i + 2] = (new_pixel & 0xFF0000) >> 16
        new_data[4 * i + 1] = (new_pixel & 0xFF00) >> 8
        new_data[4 * i + 0] = new_pixel & 0xFF

    return bytes(new_data)


cpdef bytes swapRB_RGBA8(u8[:] data):
    cdef u32 numPixels = len(data) // 4

    cdef bytearray new_data = bytearray(numPixels * 4)

    cdef u32 i

    for i in range(numPixels):
        new_data[4 * i + 0] = data[4 * i + 2]
        new_data[4 * i + 1] = data[4 * i + 1]
        new_data[4 * i + 2] = data[4 * i + 0]
        new_data[4 * i + 3] = data[4 * i + 3]

    return bytes(new_data)
