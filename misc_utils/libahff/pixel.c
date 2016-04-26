/*
 * pixel.c - Routines for converting common GL pixel formats to RGBA32.
 * Copyright (c) 2015 The Holy Constituency of the Summer Triangle.
 * All rights reserved.
 */
#include "rg_etc1wrap.h"

void copy_1bpp_luma(byte *raw, int len, byte *output) {
    memset(output, 255, len * 4);
    for (int i = 0, ctr = 0; i < len; ctr = (++i) * 4) {
        output[ctr] = raw[i];
        output[ctr + 1] = raw[i];
        output[ctr + 2] = raw[i];
    }
}

void copy_1bpp_alpha(byte *raw, int len, byte *output) {
    memset(output, 0, len * 4);
    for (int i = 0, ctr = 0; i < len; ctr = (++i) * 4) {
        output[ctr + 3] = raw[i];
    }
}

void copy_2bpp_lumalpha(byte *raw, int len, byte *output) {
    memset(output, 0, len * 2);
    for (int i = 0, ctr = 0; i < len; ctr = (i += 2) * 4) {
        output[ctr] = raw[i];
        output[ctr + 1] = raw[i];
        output[ctr + 2] = raw[i];
        output[ctr + 3] = raw[i + 1];
    }
}

void copy_2bpp_rgb565(byte *raw, int len, byte *output) {
    memset(output, 255, len * 2);
    unsigned short *pixels = (unsigned short *) raw;
    unsigned int len2 = len / 2;
    for (int i = 0, ctr = 0; i < len2; ctr = (++i) * 4) {
        unsigned short pixel = pixels[i];
        byte shift = (pixel & 0xF800) >> 8;
        output[ctr] = shift | (shift >> 5);
        shift = (pixel & 0x07E0) >> 3;
        output[ctr + 1] = shift | (shift >> 6);
        shift = (pixel & 0x001F) << 3;
        output[ctr + 2] = shift | (shift >> 5);
    }
}

void copy_2bpp_rgba5551(byte *raw, int len, byte *output) {
    unsigned short *pixels = (unsigned short *) raw;
    unsigned int len2 = len / 2;
    for (int i = 0, ctr = 0; i < len2; ctr = (++i) * 4) {
        unsigned short pixel = pixels[i];
        byte shift = (pixel & 0xF800) >> 8;
        output[ctr] = shift | (shift >> 5);
        shift = (pixel & 0x07C0) >> 3;
        output[ctr + 1] = shift | (shift >> 5);
        shift = (pixel & 0x003E) << 3;
        output[ctr + 2] = shift | (shift >> 5);
        output[ctr + 3] = (pixel % 2)? 255 : 0;
    }
}

void copy_2bpp_rgba4444(byte *raw, int len, byte *output) {
    unsigned short *pixels = (unsigned short *) raw;
    unsigned int len2 = len / 2;
    for (int i = 0, ctr = 0; i < len2; ctr = (++i) * 4) {
        unsigned short pixel = pixels[i];
        byte shift = (pixel & 0xF000) >> 8;
        output[ctr] = shift | (shift >> 4);
        shift = (pixel & 0x0F00) >> 4;
        output[ctr + 1] = shift | (shift >> 4);
        shift = pixel & 0x00F0;
        output[ctr + 2] = shift | (shift >> 4);
        shift = pixel & 0x000F;
        output[ctr + 3] = shift | (shift << 4);
    }
}

void copy_3bpp_rgb(byte *raw, int len, byte *output) {
    memset(output, 255, len + (len / 3));
    for (int i = 0, ctr = 0; i < len; ctr = (i += 3) * 4) {
        output[ctr] = raw[i];
        output[ctr + 1] = raw[i + 1];
        output[ctr + 2] = raw[i + 2];
    }
}

void copy_etc1_rgb(byte *raw, int len, byte *output, int width) {
    byte dst[4 * 4 * 4];
    byte *row1 = output,
         *row2 = row1 + (width * 4),
         *row3 = row2 + (width * 4),
         *row4 = row3 + (width * 4);
    int offset = 0;
    for (int i = 0; i < len; i += 8) {
        assert(unpack_etc1_block_c(raw + i, dst, 0) == 1);
        
        memcpy(row1 + offset, dst     , 4 * 4);
        memcpy(row2 + offset, dst + 16, 4 * 4);
        memcpy(row3 + offset, dst + 32, 4 * 4);
        memcpy(row4 + offset, dst + 48, 4 * 4);

        offset += 16;

        if (offset >= width * 4) {
            row1 = row4 + (width * 4);
            row2 = row1 + (width * 4);
            row3 = row2 + (width * 4);
            row4 = row3 + (width * 4);
            offset = 0;
        }
    }
}
