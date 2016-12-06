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

run_tess_all()
{
	type=${1}

	mkdir -p output/${type}/tesseract
	for input in input/${type}/*;
	do
		output=$(basename ${input})
		output=$(echo ${output} | sed s/.jpg//g)
		output=$(echo ${output} | sed s/.png//g)

		lang=eng
		extra_config=""
		if echo ${output} | grep digit > /dev/null ;
		then
			lang=eng # don't touch
			extra_config="digits"
		elif echo ${output} | grep french > /dev/null ;
		then lang=fra
		elif echo ${output} | grep japanese > /dev/null ;
		then lang=jpn
		fi

		run_tess ${input} output/${type}/tesseract/${output} ${lang} \
			${extra_config}
		run_tess ${input} output/${type}/tesseract/${output} ${lang} \
			batch.nochop makebox ${extra_config}
		run_tess ${input} output/${type}/tesseract/${output} ${lang} \
			hocr ${extra_config}

		mv output/${type}/tesseract/${output}.hocr \
			output/${type}/tesseract/${output}.words
		cp output/${type}/tesseract/${output}.words \
			output/${type}/tesseract/${output}.lines
	done
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

run_tess_api_all()
{
	type="$1"

	mkdir -p output/${type}/libtesseract
	for input in input/${type}/*;
	do
		output=$(basename ${input})
		output=$(echo ${output} | sed s/.jpg//g)
		output=$(echo ${output} | sed s/.png//g)

		lang=eng
		if echo ${output} | grep digit > /dev/null ;
		then
			run_tess_api ${input} output/${type}/libtesseract/${output}.txt \
				${lang} \
				DigitBuilder
			run_tess_api ${input} output/${type}/libtesseract/${output}.lines \
				${lang} \
				DigitLineBoxBuilder
		elif echo ${output} | grep french > /dev/null ;
		then lang=fra
		elif echo ${output} | grep japanese > /dev/null ;
		then lang=jpn
		fi

		run_tess_api ${input} output/${type}/libtesseract/${output}.txt ${lang} \
			TextBuilder
		run_tess_api ${input} output/${type}/libtesseract/${output}.words ${lang} \
			WordBoxBuilder
		run_tess_api ${input} output/${type}/libtesseract/${output}.lines ${lang} \
			LineBoxBuilder
	done
}

run_cuneiform()
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

	echo cuneiform ${lang_arg} ${lang} "$@" -o ${out} ${img}
	if ! cuneiform ${lang_arg} ${lang} "$@" -o ${out} ${img} > /dev/null; then
		echo "FAILED !"
	fi
}

run_cuneiform_all()
{
	type="$1"

	mkdir -p output/${type}/cuneiform
	for input in input/${type}/*;
	do
		output=$(basename ${input})
		output=$(echo ${output} | sed s/.jpg//g)
		output=$(echo ${output} | sed s/.png//g)

		lang=eng
		if echo ${output} | grep french > /dev/null ;
		then lang=fra
		elif echo ${output} | grep japanese > /dev/null ;
		then
			# skip japanese for now
			continue
		fi

		run_cuneiform ${input} output/${type}/cuneiform/${output}.txt ${lang} -f text
		run_cuneiform ${input} output/${type}/cuneiform/${output}.words ${lang} -f hocr
		run_cuneiform ${input} output/${type}/cuneiform/${output}.lines ${lang} -f hocr
	done
}

cd tests

echo "=== Tesseract sh ==="

run_tess_all real
run_tess_all specific

echo "=== Tesseract C-api ==="

run_tess_api_all real
run_tess_api_all specific

echo "=== Cuneiform ==="

run_cuneiform_all real
run_cuneiform_all specific
