#!/bin/bash
shopt -s extglob
shopt -s nullglob

# This file must only use bash builtins.
# Nothing is available in the remote chroot.

for CHARA_ID in "$1"/*; do
    for POSE in "$CHARA_ID/"+([^_]).png; do
        read ADJUST_ARGLIST < ${POSE%.png}.adjustment
        echo "SVX_APPLY_ADJUSTMENT($ADJUST_ARGLIST);" > ${POSE%.png}.json

        FACE_LIST="["
        for FILE in "${POSE%.png}"_*.png; do
            X="${POSE%.png}_"
            X=${FILE#$X}
            FACE_LIST="$FACE_LIST${X%.png},"
        done
        X=${POSE%.png}
        echo "SVX_APPLY_FACE_LIST(${X#$CHARA_ID/}, $FACE_LIST]);" >> ${POSE%.png}.json
    done
done