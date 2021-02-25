#Copyright Gian Paolo Ciceri, 2004
#Code taken from http://code.activestate.com/recipes/259177-crc64-calculate-the-cyclic-redundancy-check/
#Licensed under the PSF License
#Note: The author was probably not meant to release this under the PSF License.

# Initialisation
# 32 first bits of generator polynomial for CRC64
# the 32 lower bits are assumed to be zero

POLY64REVh = 0xd8000000
CRCTableh = [0] * 256
CRCTablel = [0] * 256
isInitialized = False


def CRC64(aString):
    global isInitialized
    crcl = 0
    crch = 0
    if (isInitialized is not True):
        isInitialized = True
        for i in range(256):
            partl = i
            parth = 0
            for j in range(8):
                rflag = partl & 1
                partl >>= 1
                if (parth & 1):
                    partl |= (1 << 31)
                parth >>= 1
                if rflag:
                    parth ^= POLY64REVh
            CRCTableh[i] = parth;
            CRCTablel[i] = partl;

    for item in aString:
        shr = 0
        shr = (crch & 0xFF) << 24
        temp1h = crch >> 8
        temp1l = (crcl >> 8) | shr
        tableindex = (crcl ^ ord(item)) & 0xFF

        crch = temp1h ^ CRCTableh[tableindex]
        crcl = temp1l ^ CRCTablel[tableindex]
    return (crch, crcl)


def CRC64digest(aString):
    return "%08X%08X" % (CRC64(aString))


assert CRC64("IHATEMATH") == (3822890454, 2600578513)
assert CRC64digest("IHATEMATH") == "E3DCADD69B01ADD1"
