#!/bin/bash
shopt -s extglob
shopt -s nullglob

for CHARA_ID in "$1"/*; do
    for FILE in "$CHARA_ID/"+([^_]).png; do
        if [[ "x$(echo ${FILE%.png}_*.png)" == "x" ]] ; then
            mogrify -trim $FILE
        else
            IFS=" " read -r -a ORIGINAL_DIMENSIONS <<< $(identify -format "%[fx:w] %[fx:h]" $FILE)
            convert $FILE -gravity South-East -background white -splice 1x0 -background black -splice 1x0 -trim -chop 1x0 +repage -background white -splice 0x1 -background black -splice 0x1 -trim -chop 0x1 +repage $(dirname $FILE)/__tmp_$(basename $FILE)
            IFS=" " read -r -a TRIMMED_DIMENSIONS <<< $(identify -format "%[fx:w] %[fx:h]" $(dirname $FILE)/__tmp_$(basename $FILE))

            BN=$(basename $FILE)
            printf "%d, -%d, -%d, %d, %d" \
                ${BN%.png} \
                $(expr ${ORIGINAL_DIMENSIONS[0]} - ${TRIMMED_DIMENSIONS[0]}) \
                $(expr ${ORIGINAL_DIMENSIONS[1]} - ${TRIMMED_DIMENSIONS[1]}) \
                ${ORIGINAL_DIMENSIONS[0]} \
                ${ORIGINAL_DIMENSIONS[1]} \
                > ${FILE%.png}.adjustment

            convert $(dirname $FILE)/__tmp_$(basename $FILE) -trim +repage $FILE
            rm $(dirname $FILE)/__tmp_$(basename $FILE)
        fi
    done
done
