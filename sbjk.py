#!/usr/bin/env python3
import requests
import os
import sqlite3
import lz4
import io
import sys
import acb
import re
import fnmatch
import functools
import subprocess
import assetbundle
import ctypes
from collections import namedtuple, OrderedDict

SESSION = requests.Session()

# yes, it is still .dylib even on linux
libahff = ctypes.cdll.LoadLibrary(
    os.path.join(os.path.dirname(__file__), "misc_utils", os.getenv("PLATFORM"), "libahff.dylib"))
libahff.ahff_encode_texdata.argtypes = [
    ctypes.c_int,     # int fmt,
    ctypes.c_int,     # int width,
    ctypes.c_int,     # int height,
    ctypes.c_size_t,  # size_t len,
    ctypes.c_char_p,  # const uint8_t *data,
    ctypes.c_char_p]  # const char *out_path
libahff.ahff_encode_texdata.restype = ctypes.c_int

def invoke_external_util(util, *args):
    util = os.path.join(os.path.dirname(__file__), "misc_utils", os.getenv("PLATFORM"), util)
    try:
        output = subprocess.check_output((util,) + args, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as inv:
        print("invoke_external_util: util exited abnormally", util, *args)
        sys.stdout.buffer.write(inv.output)

def get_resource(url, asset_name, flags):
    resp = SESSION.get(url)
    resp.raise_for_status()

    buf = resp.content
    if flags & 1:
        bio = io.BytesIO()
        bio.write(buf[4:8])
        bio.write(buf[16:])
        buf = lz4.loads(bio.getvalue())

    return buf

def noop(url, asset_name, flags):
    print("noop", asset_name)

def audio(object_id, use, index):
    a = (object_id << 40) | ((use & 0xFF) << 24) | ((index & 0xFF) << 16) | 0x11AB
    # make everything 8 bytes long for reasons
    a &= 0xFFFFFFFFFFFFFFFF
    a ^= 0x1042FC1040200700
    basename = hex(a)[2:]
    return basename

def real_extract_image_to(target, file_id_regex, file_format, only_match, url, asset_name, flags):
    buf = get_resource(url, asset_name, flags)
    tf = file_format.format(*file_id_regex.findall(asset_name))
    only_match = only_match or b"*"

    class fakefd(object):
        def __init__(self, stream):
            self.stream = stream
        def read(self):
            return self.stream

    bundle_objects = assetbundle.Asset(fakefd(buf))
    for obj in bundle_objects.objs:
        if "image data" not in obj:
            continue

        if fnmatch.fnmatch(obj["m_Name"], only_match):
            tf = os.path.join(target, tf)
            try:
                os.makedirs(os.path.dirname(tf), 0o755)
            except FileExistsError:
                pass

            data = obj["image data"]
            width, height, fmt = obj["m_Width"], obj["m_Height"], obj["m_TextureFormat"]
            libahff.ahff_encode_texdata(fmt, width, height, len(data), data, tf.encode("utf8"))

def extract_image_to(target, file_id_regex, file_format, only_match=None):
    target_dir = os.path.join(os.getenv("WORKING_DIR"), "root", target)
    try:
        os.makedirs(target_dir, 0o755)
    except FileExistsError:
        pass
    return functools.partial(real_extract_image_to, target_dir, re.compile(file_id_regex), file_format, only_match)

def process_acb(url, asset_name, flags):
    target_dir = os.path.join(os.getenv("WORKING_DIR"), "root", "va2")
    try:
        os.makedirs(target_dir, 0o755)
    except FileExistsError:
        pass

    buf = get_resource(url, asset_name, flags)

    acb_file = io.BytesIO(buf)
    acb_file.seek(0)

    utf = acb.UTFTable(acb_file)
    cue = acb.TrackList(utf)
    embedded_awb = io.BytesIO(utf.rows[0]["AwbFile"])
    data_source = acb.AFSArchive(embedded_awb)

    for track in cue.tracks:
        print("queueing", track)
        params = [int(x) for x in re.findall("0*[0-9]+", track.name)]
        if len(params) != 3:
            continue

        base = audio(*params[:3])
        name = "{0}{1}".format(base, acb.wave_type_ftable.get(track.enc_type, track.enc_type))
        with open(os.path.join(target_dir, name), "wb") as named_out_file:
            named_out_file.write(data_source.file_data_for_cue_id(track.cue_id))

    invoke_external_util("scan_dec_hca", target_dir)

def do_action_for_file(asset_name, hash, flags):
    if asset_name.endswith(".unity3d"):
        url = ASSETBBASEURL.format(hash)
    if asset_name.endswith(".acb"):
        url = SOUNDBASEURL.format(hash, os.path.dirname(asset_name))
    if asset_name.endswith(".mdb"):
        url = SQLBASEURL.format(hash)

    for key in ACTIONS:
        if fnmatch.fnmatch(asset_name, key):
            ACTIONS[key](url, asset_name, flags)
            break



ACTIONS_FAST = OrderedDict([
    ("card_bg_*_*.unity3d",         noop),
    ("card_gacha_*_*_sign.unity3d", extract_image_to("sign",           r"(?:0+)?([0-9]+)", "{0}.png")),
    ("card_petit_*.unity3d",        extract_image_to("puchi",          r"(?:0+)?([0-9]+)", "{0}.png")),
    ("card_bg_*.unity3d",           extract_image_to("spread",         r"(?:0+)?([0-9]+)", "{0}.png")),
    ("card_*_xl.unity3d",           extract_image_to("card",           r"(?:0+)?([0-9]+)", "{0}.png")),
    ("card_*_sm.unity3d",           extract_image_to("../iconcache",   r"(?:0+)?([0-9]+)", "{0}.png", b"*_m")),
    ("chara_icon_*.unity3d",        extract_image_to("icon_char",      r"(?:0+)?([0-9]+)", "{0}.png")),
])

ACTIONS_SLOW = OrderedDict([
    ("chara_*_base.unity3d",        extract_image_to("chara2",         r"(?:0+)?([0-9]+)", "{0}/{1}.png")),
    ("chara_*_face_*.unity3d",      extract_image_to("chara2",         r"(?:0+)?([0-9]+)", "{0}/{1}_{2}.png")),
    ("v/*.acb",                     process_acb),
])

ACTIONS = ACTIONS_FAST
if os.getenv("SBJK_EXEC_MODE") != "fast":
    for k, v in ACTIONS_SLOW.items():
        ACTIONS[k] = v

DBMANIFEST = "http://storage.game.starlight-stage.jp/dl/{0}/manifests"
ASSETBBASEURL = "http://storage.game.starlight-stage.jp/dl/resources/High/AssetBundles/Android/{0}"
SOUNDBASEURL = "http://storage.game.starlight-stage.jp/dl/resources/High/Sound/Common/{1}/{0}"
SQLBASEURL = "http://storage.game.starlight-stage.jp/dl/resources/Generic/{0}"
CACHE = os.path.join(os.getenv("WORKING_DIR"), "__manifestloader_cache")
try:
    os.makedirs(CACHE, 0o755)
except FileExistsError:
    pass

def batches(n, iterator):
    while 1:
        current_batch = []
        for x in range(n):
            try:
                current_batch.append(next(iterator))
            except StopIteration:
                yield current_batch
                break
        else:
            yield current_batch
            continue
        break

def filename(version, platform, asset_qual, sound_qual):
    return "{0}_{1}_{2}_{3}".format(version, platform, asset_qual, sound_qual)

def read_manifest(version, platform, asset_qual, sound_qual):
    dest_file = os.path.join(CACHE, filename(version, platform, asset_qual, sound_qual))
    if not os.path.exists(dest_file):
        acquire_manifest(version, platform, asset_qual, sound_qual, dest_file)

    conn = sqlite3.connect(dest_file)
    conn.row_factory = sqlite3.Row
    return conn

manifest_selector_t = namedtuple("manifest_selector_t", ("filename", "md5", "platform", "asset_qual", "sound_qual"))
def acquire_manifest(version, platform, asset_qual, sound_qual, dest_file):
    meta = "/".join(( DBMANIFEST.format(version), "all_dbmanifest" ))
    m = SESSION.get(meta)
    m.raise_for_status()
    mp = map(lambda x: manifest_selector_t(* x.split(",")), filter(bool, m.text.split("\n")))

    get_file = None
    for selector in mp:
        if selector.platform == platform and \
           selector.asset_qual == asset_qual and \
           selector.sound_qual == sound_qual:
            get_file = selector.filename
            break

    abso = "/".join(( DBMANIFEST.format(version), get_file ))
    resp = SESSION.get(abso)
    resp.raise_for_status()

    buf = resp.content
    bio = io.BytesIO()
    bio.write(buf[4:8])
    bio.write(buf[16:])
    data = lz4.loads(bio.getvalue())
    with open(dest_file, "wb") as write_db:
        write_db.write(data)

    return dest_file

seen_op_t = namedtuple("seen_op_t", ("is_insert", "name", "hash"))

def main(version):
    seen_db = sqlite3.connect(os.path.join(CACHE, "A_SyncCache.db"))
    seen_db.execute("CREATE TABLE IF NOT EXISTS seen (name TEXT, hash TEXT)")
    seen_db.commit()

    sql = read_manifest(version, "Android", "High", "High")
    query = "SELECT name, hash, attr FROM manifests WHERE ({0})".format(
        " OR ".join("name GLOB ?" for glob in ACTIONS))
    all_wanted_files = sql.execute(query, tuple(ACTIONS.keys()))

    for batch in batches(100, all_wanted_files):
        seen_ops = []

        cm = seen_db.execute("SELECT name, hash FROM seen WHERE name IN ({0})".format(
            ",".join("?" for row in batch)
        ), tuple(row["name"] for row in batch))
        cm = {row[0]: row[1] for row in cm}

        for row in batch:
            hashid = cm.get(row["name"])
            if hashid != row["hash"]:
                print(row["name"])

                try:
                    do_action_for_file(row["name"], row["hash"], row["attr"])
                except Exception as e:
                    print(e)
                    continue

                if hashid is None:
                    seen_ops.append(seen_op_t(1, row["name"], row["hash"]))
                else:
                    seen_ops.append(seen_op_t(0, row["name"], row["hash"]))

        for op in seen_ops:
            if op.is_insert:
                q = "INSERT INTO seen VALUES (:name, :hash)"
            else:
                q = "UPDATE seen SET hash = :hash WHERE name = :name"
            seen_db.execute(q, {"name": op.name, "hash": op.hash})

        seen_db.commit()
    sql.close()
    seen_db.close()

if __name__ == '__main__':
    main(int(sys.argv[1]))
