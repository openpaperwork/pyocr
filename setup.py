#!/usr/bin/env python

from setuptools import setup

setup(name="pyocr",
      version="0.1.2-git",
      description="A Python wrapper for OCR (Tesseract, Cuneiform, etc)",
      author="Jerome Flesch",
      author_email="jflesch@gmail.com",
      packages=['pyocr'],
      package_dir={ 'pyocr': 'src' },
      data_files=[],
      scripts=[],
      install_requires=[
          "PIL"
      ],
     )

