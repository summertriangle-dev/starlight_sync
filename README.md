# sbjk

The toolset used to maintain the image server for starlight.kirara.ca.

### Getting started

Compile the LAME encoder and copy it into `misc_utils/<platform>`. The
program we want is the `lame` binary in `frontend`.

Then compile the HCA decoder (make sure to pre-bake the keys as
`scan_dec_hca` doesn't provide them on the CLI) and put `hca_decoder`
in `misc_utils/<platform>`.

Configure the environment as you did for sparklebox:

    export TRANSIENT_DIR_POINTER=TRANSIENT_DATA_DIR
    export TRANSIENT_DATA_DIR=_data/transient

    # the name of a folder in misc_utils. Platform binaries
    # needed by SBJK will be loaded from there.
    export PLATFORM=macosx

    # see sparklebox config
    export VC_ACCOUNT=...
    export VC_AES_KEY=...
    export VC_SID_SALT=...

    # truth version number if you don't have auto-update secrets
    export SIMULATED_VERSION=xxxxxxxx

    # rsync/scp format
    export SYNCREMOTE=cdn@ssh.static.com:/webroot/

    # generated with ssh-keygen; it's the big file, not the
    # small one that ends in .pub
    export SSH_PRIVATE_KEY=/path/to/some/ssh/key

Now you can set a cron job to run `kickoff` and we will automatically
update from the CDN.

### Programs

`acb.py <path-to-acb-file> <path-to-out-dir>`

Extracts HCA tracks from ACB files with embedded data.

`assetbundle.py <path-to-unity3d-file> [output file]`

Extracts images from Unity assetbundles.
Note: Currently broken for CLI usage. We also use ctypes to call ahff2png
for image saving instead of the PIL, because it provides better compression.

`iconsheet_new.py <path-to-iconcache> <path-to-iconsheet-cache-folder> <path-to-output-folder>`

Incrementally combine the iconcache into sheets of 8x8 icons each. Uses a cache
to speed things up.

`kickoff`

Check the server version, and run SBJK, iconsheet, and rsync if it changed.

`sbjk.py <version>`

Downloads changed files from CDN and saves them to the `$WORKING_DIR`.
Requires the environment to be set.

`simver <version>`

If `$SIMULATED_VERSION` is set, print that. Otherwise, prints its first
argument. This lets you pin the server version to something when running
kickoff.

`speculate.py <hint>`

Check for new data that hasn't officially been released through the API
yet. Given a hint of 10014700, looks for 10014800, 10014710, and 10014750
in that order. Print the first one found.

`versioncheck.py <current-version>`

Check for new data through the official API. Requires `VC_*` be set.
Prints the current game version if it can, otherwise prints `current-version.`

### Adding new things to SBJK

The first thing you need to do is write some code to run on your file(s).
You should have a callable objects that takes:

- the full URL to the resource
- the file name of the resource
- the resource flags (1 is the LZ4 compressed attribute).

This function downloads any assets given and saves it to the `/things` directory
on the image server. It makes use of the `get_resource`, which downloads the
asset and decompresses LZ4 if needed.

```python
    def process_my_file(url, asset_name, flags):
        target_file = os.path.join(os.getenv("WORKING_DIR"), "root", "things", asset_name)
        buf = get_resource(url, asset_name, flags)

        with open(target_file, "wb") as named_out_file:
            named_out_file.write(buf)
```

To make SBJK use your function, add an entry to the ACTIONS list. Entries are a
2-tuple with a file pattern (similar to shell glob) and the callable.

    ("my_*.file", process_my_file)

### Credits

- The guy who wrote the HCA decoder
- @marcan for the [lightweight asset bundle decoder and open-source API client]
  (https://github.com/marcan/deresuteme)
