/*
 * ahff2png.c - disunityed file tool
 * Copyright (c) 2015 The Holy Constituency of the Summer Triangle.
 * All rights reserved.
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <assert.h>
#include <fcntl.h>

#include "lodepng.h"

typedef union {
    unsigned char b[4];
    uint32_t n;
} byte_addressable_uint32;
typedef unsigned char byte;

// the Ad-Hoc File Format is intentionally very simple so i don't have
// to write so much java
// packed should have no effect, this is just for safety reasons
typedef union {
    byte b[16];
    struct __attribute__((packed)) {
        uint32_t width;
        uint32_t height;
        uint32_t datsize;
        uint32_t pixel_format;
    } s;
} ahff_header_t;

enum /* pixel_format_t */ {
    A8 = 1,
    RGB24 = 3,
    RGBA32 = 4,
    ARGB32 = 5,
    RGB565 = 7,
    RGBA4444 = 13,
    ETC1RGB = 34,
};

#define READ_FULLY(fd, buf, size) do { \
    size_t _eval_one = (size); \
    size_t nread = read(fd, buf, _eval_one); \
    assert(nread == _eval_one || !"READ_FULLY did not read fully."); \
} while(0)

#include "pixel.c"

void flip_image_sideways(byte *buf, uint32_t width, uint32_t height) {
    byte *work = malloc(width * 4);
    byte *worp = work;

    for (int row = 0; row < height; ++row) {
        byte *crow = buf + (row * width * 4);
        worp = work;

        for (size_t i = (width - 1) * 4; i > 0; i -= 4) {
            memcpy(worp, crow + i, 4);
            worp += 4;
        }

        memcpy(crow, work, width * 4);
    }

    free(work);
}

void flip_image_upside_down(byte *buf, uint32_t width, uint32_t height) {
    byte *work = malloc(width * 4);

    for (int row = 0, target_row = height - 1; row < (height / 2); ++row, --target_row) {
        memcpy(work, buf + (target_row * width * 4), width * 4);
        memcpy(buf + (target_row * width * 4), buf + (row * width * 4), width * 4);
        memcpy(buf + (row * width * 4), work, width * 4);
    }

    free(work);
}

int ahff_encode_texdata(int fmt,
                        int width, int height,
                        size_t len, const uint8_t *data,
                        const char *out_path) {
    unsigned char *out = calloc(width * height, 4);
    uint32_t point_count = width * height;
    uint32_t expect_size = 0;
    int has_alpha = 1;

    switch (fmt) {
        case A8:
            expect_size = point_count;
            copy_1bpp_alpha(data, expect_size, out);
            break;
        case RGB24:
            expect_size = point_count * 3;
            copy_3bpp_rgb(data, expect_size, out);
            has_alpha = 0;
            break;
        case RGB565:
            expect_size = point_count * 2;
            copy_2bpp_rgb565(data, expect_size, out);
            has_alpha = 0;
            break;
        case RGBA4444:
            expect_size = point_count * 2;
            copy_2bpp_rgba4444(data, expect_size, out);
            break;
        case RGBA32:
        case ARGB32: {
            expect_size = point_count * 4;
            memcpy(out, data, expect_size);

            if (fmt == ARGB32) {
                for (uint8_t *pbase = out; pbase < (out + expect_size); pbase += 4) {
                    uint8_t tmp = pbase[0];
                    pbase[0] = pbase[1];
                    pbase[1] = pbase[2];
                    pbase[2] = pbase[3];
                    pbase[3] = tmp;
                }
            }

            break;
        }
        case ETC1RGB:
            /* ETC1 encodes 4x4 blocks.
             * So w and h must be multiples of 4. */
            assert(width % 4 == 0);
            assert(height % 4 == 0);
            expect_size = point_count / 2;
            copy_etc1_rgb(data, expect_size, out, width);
            has_alpha = 0;
            break;
        default:
            fprintf(stderr, "unknown itype %d\n", fmt);
            goto end;
    }

    // flip_image_sideways(out, info.width, info.height);
    flip_image_upside_down(out, width, height);
    lodepng_encode32_file(out_path, out, width, height);

  end:
    free(out);
    return 0;
}
