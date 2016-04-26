#include "rg_etc1.h"

extern "C" {

int unpack_etc1_block_c(const unsigned char *pETC1_block, unsigned char *pDst_pixels_rgba, int preserve_alpha) {
    return rg_etc1::unpack_etc1_block(pETC1_block, (unsigned int *)pDst_pixels_rgba, preserve_alpha) ? 1 : 0;
}

}
