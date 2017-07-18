# Use Python 3.4+

BCn_formats = [0x31, 0x431, 0x32, 0x432, 0x33, 0x433, 0x34, 0x234, 0x35, 0x235]


def deswizzle(width, height, height2, format_, tileMode, swizzle_, pitch, bpp, data):
    result = bytearray(data)

    if format_ in BCn_formats:
        width = (width + 3) // 4
        height = (height + 3) // 4

    for y in range(height):
        for x in range(width):
            pipeSwizzle = (swizzle_ >> 8) & 1
            bankSwizzle = (swizzle_ >> 9) & 3

            if tileMode == 0 or tileMode == 1:
                pos = AddrLib_computeSurfaceAddrFromCoordLinear(x, y, bpp, pitch)
            elif tileMode == 2 or tileMode == 3:
                pos = AddrLib_computeSurfaceAddrFromCoordMicroTiled(x, y, bpp, pitch, tileMode)
            else:
                pos = AddrLib_computeSurfaceAddrFromCoordMacroTiled(x, y, bpp, pitch, height2, tileMode,
                                                                              pipeSwizzle, bankSwizzle)
            bpp2 = bpp
            bpp2 //= 8

            pos_ = (y * width + x) * bpp2

            if (pos_ < len(data)) and (pos < len(data)):
                result[pos_:pos_ + bpp2] = data[pos:pos + bpp2]

    return result


def swizzle(width, height, height2, format_, tileMode, swizzle_, pitch, bpp, data):
    result = bytearray(data)

    if format_ in BCn_formats:
        width = (width + 3) // 4
        height = (height + 3) // 4

    for y in range(height):
        for x in range(width):
            pipeSwizzle = (swizzle_ >> 8) & 1
            bankSwizzle = (swizzle_ >> 9) & 3

            if tileMode == 0 or tileMode == 1:
                pos = AddrLib_computeSurfaceAddrFromCoordLinear(x, y, bpp, pitch)
            elif tileMode == 2 or tileMode == 3:
                pos = AddrLib_computeSurfaceAddrFromCoordMicroTiled(x, y, bpp, pitch, tileMode)
            else:
                pos = AddrLib_computeSurfaceAddrFromCoordMacroTiled(x, y, bpp, pitch, height2, tileMode,
                                                                              pipeSwizzle, bankSwizzle)

            bpp2 = bpp
            bpp2 //= 8

            pos_ = (y * width + x) * bpp2

            if (pos < len(data)) and (pos_ < len(data)):
                result[pos:pos + bpp2] = data[pos_:pos_ + bpp2]

    return result


# Credits:
#  -AddrLib: actual code
#  -Exzap: modifying code to apply to Wii U textures
#  -AboodXD: porting, code improvements and cleaning up

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

MicroTilePixels = 64

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
    thickness = 1

    if tileMode == 3 or tileMode == 7 or tileMode == 11 or tileMode == 13 or tileMode == 15:
        thickness = 4

    elif tileMode == 16 or tileMode == 17:
        thickness = 8

    return thickness


def computePixelIndexWithinMicroTile(x, y, bpp, tileMode, z=0):
    pixelBit6 = 0
    pixelBit7 = 0
    pixelBit8 = 0
    thickness = computeSurfaceThickness(tileMode)

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

    elif bpp == 0x20 or bpp == 0x60:
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

    return ((pixelBit8 << 8) | (pixelBit7 << 7) | (pixelBit6 << 6) |
            32 * pixelBit5 | 16 * pixelBit4 | 8 * pixelBit3 |
            4 * pixelBit2 | pixelBit0 | 2 * pixelBit1)


def computePipeFromCoordWoRotation(x, y):
    # hardcoded to assume 2 pipes
    return ((y >> 3) ^ (x >> 3)) & 1


def computeBankFromCoordWoRotation(x, y):
    numPipes = m_pipes
    numBanks = m_banks
    bank = 0

    if numBanks == 4:
        bankBit0 = ((y // (16 * numPipes)) ^ (x >> 3)) & 1
        bank = bankBit0 | 2 * (((y // (8 * numPipes)) ^ (x >> 4)) & 1)

    elif numBanks == 8:
        bankBit0a = ((y // (32 * numPipes)) ^ (x >> 3)) & 1
        bank = (bankBit0a | 2 * (((y // (32 * numPipes)) ^ (y // (16 * numPipes) ^ (x >> 4))) & 1) |
            4 * (((y // (8 * numPipes)) ^ (x >> 5)) & 1))

    return bank


def isThickMacroTiled(tileMode):
    thickMacroTiled = 0

    if tileMode in [7, 11, 13, 15]:
        thickMacroTiled = 1

    return thickMacroTiled


def isBankSwappedTileMode(tileMode):
    bankSwapped = 0

    if tileMode in [8, 9, 10, 11, 14, 15]:
        bankSwapped = 1

    return bankSwapped


def computeMacroTileAspectRatio(tileMode):
    ratio = 1

    if tileMode in [8, 12, 14]:
        ratio = 1

    elif tileMode in [5, 9]:
        ratio = 2

    elif tileMode in [6, 10]:
        ratio = 4

    return ratio


def computeSurfaceBankSwappedWidth(tileMode, bpp, pitch, numSamples=1):
    if isBankSwappedTileMode(tileMode) == 0: return 0

    numBanks = m_banks
    numPipes = m_pipes
    swapSize = m_swapSize
    rowSize = m_rowSize
    splitSize = m_splitSize
    groupSize = m_pipeInterleaveBytes
    bytesPerSample = 8 * bpp

    try:
        samplesPerTile = splitSize // bytesPerSample
        slicesPerTile = max(1, numSamples // samplesPerTile)
    except ZeroDivisionError:
        slicesPerTile = 1

    if isThickMacroTiled(tileMode) != 0:
        numSamples = 4

    bytesPerTileSlice = numSamples * bytesPerSample // slicesPerTile

    factor = computeMacroTileAspectRatio(tileMode)
    swapTiles = max(1, (swapSize >> 1) // bpp)

    swapWidth = swapTiles * 8 * numBanks
    heightBytes = numSamples * factor * numPipes * bpp // slicesPerTile
    swapMax = numPipes * numBanks * rowSize // heightBytes
    swapMin = groupSize * 8 * numBanks // bytesPerTileSlice

    bankSwapWidth = min(swapMax, max(swapMin, swapWidth))

    while not bankSwapWidth < (2 * pitch):
        bankSwapWidth >>= 1

    return bankSwapWidth


def AddrLib_computeSurfaceAddrFromCoordLinear(x, y, bpp, pitch):
    rowOffset = y * pitch
    pixOffset = x

    addr = (rowOffset + pixOffset) * bpp
    addr //= 8

    return addr


def AddrLib_computeSurfaceAddrFromCoordMicroTiled(x, y, bpp, pitch, tileMode):
    microTileThickness = 1

    if tileMode == 3:
        microTileThickness = 4

    microTileBytes = (MicroTilePixels * microTileThickness * bpp + 7) // 8
    microTilesPerRow = pitch >> 3
    microTileIndexX = x >> 3
    microTileIndexY = y >> 3

    microTileOffset = microTileBytes * (microTileIndexX + microTileIndexY * microTilesPerRow)

    pixelIndex = computePixelIndexWithinMicroTile(x, y, bpp, tileMode)

    pixelOffset = bpp * pixelIndex

    pixelOffset >>= 3

    return pixelOffset + microTileOffset


def AddrLib_computeSurfaceAddrFromCoordMacroTiled(x, y, bpp, pitch, height, tileMode, pipeSwizzle, bankSwizzle):
    numPipes = m_pipes
    numBanks = m_banks
    numGroupBits = m_pipeInterleaveBytesBitcount
    numPipeBits = m_pipesBitcount
    numBankBits = m_banksBitcount

    microTileThickness = computeSurfaceThickness(tileMode)

    microTileBits = bpp * (microTileThickness * MicroTilePixels)
    microTileBytes = (microTileBits + 7) // 8

    pixelIndex = computePixelIndexWithinMicroTile(x, y, bpp, tileMode)

    pixelOffset = bpp * pixelIndex

    elemOffset = pixelOffset

    bytesPerSample = microTileBytes
    if microTileBytes <= m_splitSize:
        numSamples = 1
        sampleSlice = 0
    else:
        samplesPerSlice = m_splitSize // bytesPerSample
        numSampleSplits = max(1, 1 // samplesPerSlice)
        numSamples = samplesPerSlice
        sampleSlice = elemOffset // (microTileBits // numSampleSplits)
        elemOffset %= microTileBits // numSampleSplits
    elemOffset += 7
    elemOffset //= 8

    pipe = computePipeFromCoordWoRotation(x, y)
    bank = computeBankFromCoordWoRotation(x, y)

    bankPipe = pipe + numPipes * bank

    swizzle_ = pipeSwizzle + numPipes * bankSwizzle

    bankPipe ^= numPipes * sampleSlice * ((numBanks >> 1) + 1) ^ swizzle_
    bankPipe %= numPipes * numBanks
    pipe = bankPipe % numPipes
    bank = bankPipe // numPipes

    sliceBytes = (height * pitch * microTileThickness * bpp * numSamples + 7) // 8
    sliceOffset = sliceBytes * (sampleSlice // microTileThickness)

    macroTilePitch = 8 * m_banks
    macroTileHeight = 8 * m_pipes

    if tileMode == 5 or tileMode == 9:  # GX2_TILE_MODE_2D_TILED_THIN4 and GX2_TILE_MODE_2B_TILED_THIN2
        macroTilePitch >>= 1
        macroTileHeight *= 2

    elif tileMode == 6 or tileMode == 10:  # GX2_TILE_MODE_2D_TILED_THIN4 and GX2_TILE_MODE_2B_TILED_THIN4
        macroTilePitch >>= 2
        macroTileHeight *= 4

    macroTilesPerRow = pitch // macroTilePitch
    macroTileBytes = (numSamples * microTileThickness * bpp * macroTileHeight * macroTilePitch + 7) // 8
    macroTileIndexX = x // macroTilePitch
    macroTileIndexY = y // macroTileHeight
    macroTileOffset = (macroTileIndexX + macroTilesPerRow * macroTileIndexY) * macroTileBytes

    if tileMode == 8 or tileMode == 9 or tileMode == 10 or tileMode == 11 or tileMode == 14 or tileMode == 15:
        bankSwapOrder = [0, 1, 3, 2, 6, 7, 5, 4, 0, 0]
        bankSwapWidth = computeSurfaceBankSwappedWidth(tileMode, bpp, pitch)
        swapIndex = macroTilePitch * macroTileIndexX // bankSwapWidth
        bank ^= bankSwapOrder[swapIndex & (m_banks - 1)]

    groupMask = ((1 << numGroupBits) - 1)

    numSwizzleBits = (numBankBits + numPipeBits)

    totalOffset = (elemOffset + ((macroTileOffset + sliceOffset) >> numSwizzleBits))

    offsetHigh = (totalOffset & ~groupMask) << numSwizzleBits
    offsetLow = groupMask & totalOffset

    pipeBits = pipe << numGroupBits
    bankBits = bank << (numPipeBits + numGroupBits)

    return bankBits | pipeBits | offsetLow | offsetHigh
