#!/bin/sh

run_tess()
{
	img="$1"
	shift
	out="$1"
	shift
	lang="$1"
	shift

	lang_arg=""
	if [ -n "${lang}" ]; then
		lang_arg=-l
	fi

	echo tesseract ${img} ${out} ${lang_arg} ${lang} $@
	if ! tesseract ${img} ${out} ${lang_arg} ${lang} $@ > /dev/null 2>&1
	then
		echo "FAILED !"
	fi
}

run_tess_capi()
{
	img="$1"
	shift
	out="$1"
	shift
	lang="$1"
	shift
	builder="$1"
	shift

	echo "${img} --> ${out} (${lang} / ${builder})"

	lang_arg=""
	if [ -n "${lang}" ]; then
		lang_arg=-l
	fi

cat << EOF | python3
from PIL import Image
from pyocr import tesseract_capi
from pyocr import builders

img = Image.open("${img}")
builder = builders.${builder}()

out = tesseract_capi.image_to_string(img, lang="${lang}", builder=builder)

with open("${out}", "w") as fd:
    builder.write_file(fd, out)
EOF
}

cd tests

echo "=== Tesseract sh ==="

run_tess data/test.png tesseract/test eng
run_tess data/test.png tesseract/test eng batch.nochop makebox
run_tess data/test.png tesseract/test eng hocr
mv tesseract/test.hocr tesseract/test.words
cp tesseract/test.words tesseract/test.lines

run_tess data/test-digits.png tesseract/test-digits eng digits

run_tess data/test-european.jpg tesseract/test-european eng
run_tess data/test-european.jpg tesseract/test-european eng batch.nochop makebox
run_tess data/test-european.jpg tesseract/test-european eng hocr
mv tesseract/test-european.hocr tesseract/test-european.words
cp tesseract/test-european.words tesseract/test-european.lines

run_tess data/test-french.jpg tesseract/test-french fra
run_tess data/test-french.jpg tesseract/test-french fra batch.nochop makebox
run_tess data/test-french.jpg tesseract/test-french fra hocr
mv tesseract/test-french.hocr tesseract/test-french.words
cp tesseract/test-french.words tesseract/test-french.lines

run_tess data/test-japanese.jpg tesseract/test-japanese jpn
run_tess data/test-japanese.jpg tesseract/test-japanese jpn batch.nochop makebox
run_tess data/test-japanese.jpg tesseract/test-japanese jpn hocr
mv tesseract/test-japanese.hocr tesseract/test-japanese.words
cp tesseract/test-japanese.words tesseract/test-japanese.lines

echo "=== Tesseract C-api ==="

run_tess_capi data/test.png tesseract_capi/test.txt eng TextBuilder
run_tess_capi data/test.png tesseract_capi/test.words eng WordBoxBuilder
run_tess_capi data/test.png tesseract_capi/test.lines eng LineBoxBuilder

run_tess_capi data/test-european.jpg tesseract_capi/test-european.txt eng TextBuilder
run_tess_capi data/test-european.jpg tesseract_capi/test-european.words eng WordBoxBuilder
run_tess_capi data/test-european.jpg tesseract_capi/test-european.lines eng LineBoxBuilder

run_tess_capi data/test-french.jpg tesseract_capi/test-french.txt fra TextBuilder
run_tess_capi data/test-french.jpg tesseract_capi/test-french.words fra WordBoxBuilder
run_tess_capi data/test-french.jpg tesseract_capi/test-french.lines fra LineBoxBuilder

run_tess_capi data/test-japanese.jpg tesseract_capi/test-japanese.txt jpn TextBuilder
run_tess_capi data/test-japanese.jpg tesseract_capi/test-japanese.words jpn WordBoxBuilder
run_tess_capi data/test-japanese.jpg tesseract_capi/test-japanese.lines jpn LineBoxBuilder
