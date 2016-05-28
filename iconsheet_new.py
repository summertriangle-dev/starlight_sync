#!/usr/bin/env python3
import sys
import os
import itertools
import subprocess
import json
import binascii
import re

libexec = os.path.join(os.path.dirname(os.path.realpath(__file__)), "misc_utils", os.getenv("PLATFORM"))

w = 48
h = 48

matrix_w = 8
matrix_h = 8

def coords_for_position(ind):
    return (ind % matrix_w) * w, (ind // matrix_h) * h

def composite_images(images, cache, out):
    try:
        with open(cache, "r") as manifest:
            l = json.load(manifest)
    except (IOError, ValueError):
        l = None

    if l == images:
        print("looks fine to me:", out)
        return

    args = [os.path.join(libexec, "make_icon_sheet"), out]
    args.extend(images)
    subprocess.call(args, stdout=subprocess.DEVNULL)

    args[0] = os.path.join(libexec, "make_icon_sheet2")
    args[1] = args[1].replace(".png", "@2x.jpg")
    subprocess.call(args, stdout=subprocess.DEVNULL)

    with open(cache, "w") as manifest:
        json.dump([i for i in images], manifest)

def do(this_sect, composite_args, cache, odir, image_count, css, css2):
    composite_images(composite_args,
        os.path.join(cache, "icons_{0}.png.cache".format(image_count)),
        os.path.join(odir, "icons_{0}.png".format(image_count)))
    random = binascii.hexlify(os.urandom(16)).decode("utf8")
    for i, id in enumerate(this_sect):
        px, py = coords_for_position(i)
        css.write(".icon.icon_{0} {{ background-image:url(\"icons_{3}.png?{4}\"); background-position:-{1}px -{2}px; }}\n".format(
            id, px, py, image_count, random))
        css2.write(".icon.icon_{0} {{ background:url(\"icons_{3}@2x.jpg?{4}\") -{1}px -{2}px/384px 384px; }}\n".format(
            id, px, py, image_count, random))
    del this_sect[:]
    del composite_args[:]
    return image_count + 1

def do_if_full(this_sect, composite_args, cache, odir, image_count, css, css2):
    if len(this_sect) == matrix_h * matrix_w:
        return do(this_sect, composite_args, cache, odir, image_count, css, css2)
    return image_count

HIDPI_CSS_HEADER = """\
@media only screen and (-webkit-min-device-pixel-ratio: 1.3), 
    only screen and (-o-min-device-pixel-ratio: 13/10), 
    only screen and (min-resolution: 120dpi) {"""
def gen_icon_sheets(root, cache, odir, css, css2):
    css2.write(HIDPI_CSS_HEADER + "\n")
    this_sect = []
    composite_args = []
    image_count = 0

    gex = re.compile("^([0-9]+).png$")
    for image in filter(lambda y: gex.match(y), os.listdir(root)):
        this_sect.append(gex.match(image).group(1))
        composite_args.append(os.path.join(root, image))
        image_count = do_if_full(this_sect, composite_args, cache, odir, image_count, css, css2)

    do(this_sect, composite_args, cache, odir, image_count, css, css2)
    css2.write("}")

def main(root, cache, odir):
    with open(os.path.join(odir, "icons.css"), "w") as css, open(os.path.join(odir, "icons@2x.css"), "w") as css2:
        gen_icon_sheets(root, cache, odir, css, css2)

if __name__ == "__main__":
    import plac
    plac.call(main)
