#!/usr/bin/env python3
import sys
import requests

URL_BASE = "http://storage.game.starlight-stage.jp/dl/{0}/manifests/all_dbmanifest"

version = int(sys.argv[1])
next_major = (version + 100) - (version % 100)
next_minor50 = (version + 50) - (version % 50)
next_minor = (version + 10)
speculated_versions = [next_major, next_minor, next_minor50]

for ver in speculated_versions:
    if requests.head(URL_BASE.format(ver)).status_code != 404:
        print(ver)
        break
else:
    print(version)