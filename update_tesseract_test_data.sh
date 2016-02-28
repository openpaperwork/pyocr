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

run_tess_api()
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
from pyocr import libtesseract
from pyocr import builders

img = Image.open("${img}")
builder = builders.${builder}()

out = libtesseract.image_to_string(img, lang="${lang}", builder=builder)

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

run_libtess data/test.png libtesseract/test.txt eng TextBuilder
run_libtess data/test.png libtesseract/test.words eng WordBoxBuilder
run_libtess data/test.png libtesseract/test.lines eng LineBoxBuilder

run_libtess data/test-european.jpg libtesseract/test-european.txt eng TextBuilder
run_libtess data/test-european.jpg libtesseract/test-european.words eng WordBoxBuilder
run_libtess data/test-european.jpg libtesseract/test-european.lines eng LineBoxBuilder

run_libtess data/test-french.jpg libtesseract/test-french.txt fra TextBuilder
run_libtess data/test-french.jpg libtesseract/test-french.words fra WordBoxBuilder
run_libtess data/test-french.jpg libtesseract/test-french.lines fra LineBoxBuilder

run_libtess data/test-japanese.jpg libtesseract/test-japanese.txt jpn TextBuilder
run_libtess data/test-japanese.jpg libtesseract/test-japanese.words jpn WordBoxBuilder
run_libtess data/test-japanese.jpg libtesseract/test-japanese.lines jpn LineBoxBuilder
