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

    with open(cache, "w") as manifest:
        json.dump([i for i in images], manifest)

def do(this_sect, composite_args, cache, odir, image_count, css):
    composite_images(composite_args,
        os.path.join(cache, "icons_{0}.png.cache".format(image_count)),
        os.path.join(odir, "icons_{0}.png".format(image_count)))
    random = binascii.hexlify(os.urandom(16)).decode("utf8")
    for i, id in enumerate(this_sect):
        px, py = coords_for_position(i)
        css.write(".icon.icon_{0} {{ background-image:url(\"icons_{3}.png?{4}\"); background-position:-{1}px -{2}px; }}\n".format(
            id, px, py, image_count, random))
    del this_sect[:]
    del composite_args[:]
    return image_count + 1

def do_if_full(this_sect, composite_args, cache, odir, image_count, css):
    if len(this_sect) == matrix_h * matrix_w:
        return do(this_sect, composite_args, cache, odir, image_count, css)
    return image_count

def gen_icon_sheets(root, cache, odir, css):
    this_sect = []
    composite_args = []
    image_count = 0

    gex = re.compile("^([0-9]+).png$")
    for image in filter(lambda y: gex.match(y), os.listdir(root)):
        this_sect.append(gex.match(image).group(1))
        composite_args.append(os.path.join(root, image))
        image_count = do_if_full(this_sect, composite_args, cache, odir, image_count, css)

    do(this_sect, composite_args, cache, odir, image_count, css)

def main(root, cache, odir):
    with open(os.path.join(odir, "icons.css"), "w") as css:
        gen_icon_sheets(root, cache, odir, css)

if __name__ == "__main__":
    import plac
    plac.call(main)
