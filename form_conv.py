#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright © 2016-2018 AboodXD

################################################################
################################################################


def toGX2rgb5a1(data):
    numPixels = len(data) // 2

    new_data = bytearray(numPixels * 2)

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


def toDDSrgb5a1(data):
    numPixels = len(data) // 2

    new_data = bytearray(numPixels * 2)

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


def rgb8torgbx8(data):
    numPixels = len(data) // 3

    new_data = bytearray(numPixels * 4)

    for i in range(numPixels):
        new_data[4 * i + 0] = data[3 * i + 0]
        new_data[4 * i + 1] = data[3 * i + 1]
        new_data[4 * i + 2] = data[3 * i + 2]
        new_data[4 * i + 3] = 0xFF

    return bytes(new_data)


def torgba8(data, bytesPerPixel, compSel):
    assert bytesPerPixel <= 4

    numPixels = len(data) // bytesPerPixel

    new_data = bytearray(numPixels * 4)

    for i in range(numPixels):
        pixel = [255, 255, 255, 255, 0, 255]
        for z in range(bytesPerPixel):
            pixel[z] = data[bytesPerPixel * i + z]

        new_data[4 * i + 0] = pixel[compSel[0]]
        new_data[4 * i + 1] = pixel[compSel[1]]
        new_data[4 * i + 2] = pixel[compSel[2]]
        new_data[4 * i + 3] = pixel[compSel[3]]

    return bytes(new_data)


def swapRB_RGB565(data):
    numPixels = len(data) // 2

    new_data = bytearray(numPixels * 2)

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


def swapRB_RGB5A1(data):
    numPixels = len(data) // 2

    new_data = bytearray(numPixels * 2)

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


def swapRB_RGBA4(data):
    numPixels = len(data) // 2

    new_data = bytearray(numPixels * 2)

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


def swapRB_RGB10A2(data):
    numPixels = len(data) // 4

    new_data = bytearray(numPixels * 4)

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


def swapRB_RGBA8(data):
    numPixels = len(data) // 4

    new_data = bytearray(numPixels * 4)

    for i in range(numPixels):
        new_data[4 * i + 0] = data[4 * i + 2]
        new_data[4 * i + 1] = data[4 * i + 1]
        new_data[4 * i + 2] = data[4 * i + 0]
        new_data[4 * i + 3] = data[4 * i + 3]

    return bytes(new_data)
