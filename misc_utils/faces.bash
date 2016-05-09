#!/bin/bash
shopt -s extglob

for CHARA_ID in "$1"/*; do
    for FILE in "$CHARA_ID/"+([^_]).png; do
        IFS=" " read -r -a ORIGINAL_DIMENSIONS <<< $(identify -format "%[fx:w] %[fx:h]" $FILE)
        mogrify -gravity South-East -background white -splice 1x0 -background black -splice 1x0 -trim -chop 1x0 -background white -splice 0x1 -background black -splice 0x1 -trim +repage -chop 0x1 $FILE
        IFS=" " read -r -a TRIMMED_DIMENSIONS <<< $(identify -format "%[fx:w] %[fx:h]" $FILE)

        BN=$(basename $FILE)
        printf "SVX_APPLY_ADJUSTMENT(%d, -%d, -%d);\n" \
            ${BN%.png} \
            $(expr ${ORIGINAL_DIMENSIONS[0]} - ${TRIMMED_DIMENSIONS[0]}) \
            $(expr ${ORIGINAL_DIMENSIONS[1]} - ${TRIMMED_DIMENSIONS[1]}) \
            >> ${FILE%.png}.json

        mogrify -trim $FILE
    done
done