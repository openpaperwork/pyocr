#!/usr/bin/env python2

from distutils.core import setup

setup(name="pyocr",
      version="0.1",
      description="A Python wrapper for OCR (Tesseract, Cuneiform, etc)",
      author="Jerome Flesch",
      author_email="jflesch@gmail.com",
      packages=['pyocr'],
      package_dir={ 'pyocr': 'src' },
      data_files=[],
      scripts=[],
     )

