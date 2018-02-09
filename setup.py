#!/usr/bin/env python

import sys
from setuptools import setup

try:
    with open("src/pyocr/_version.py", "r") as file_descriptor:
        version = file_descriptor.read().strip()
        version = version.split(" ")[2][1:-1]
    print("PyOCR version: {}".format(version))
    if "-" in version:
        version = version.split("-")[0]
except FileNotFoundError:
    print("ERROR: _version.py file is missing")
    print("ERROR: Please run 'make version' first")
    sys.exit(1)

setup(
    name="pyocr",
    version=version,
    description=("A Python wrapper for OCR engines (Tesseract, Cuneiform,"
                 " etc)"),
    keywords="tesseract cuneiform ocr",
    url="https://github.com/openpaperwork/pyocr",
    download_url=(
        "https://github.com/openpaperwork/pyocr/archive/"
        "{}.zip".format(version)
    ),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 or later"
        " (GPLv3+)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Topic :: Multimedia :: Graphics :: Capture :: Scanners",
        "Topic :: Multimedia :: Graphics :: Graphics Conversion",
        "Topic :: Scientific/Engineering :: Image Recognition",
    ],
    license="GPLv3+",
    author="Jerome Flesch",
    author_email="jflesch@openpaper.work",
    packages=[
        'pyocr',
        'pyocr.libtesseract',
    ],
    package_dir={
        'pyocr': 'src/pyocr',
        'pyocr.libtesseract': 'src/pyocr/libtesseract',
    },
    data_files=[],
    scripts=[],
    zip_safe=True,
    install_requires=[
        "Pillow",
        "six",
    ],
)
