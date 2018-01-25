#!/bin/sh

ret=0


for pyver in python3 python2 ; do
    echo "# Testing with ${pyver}"
    rm -rf venv-${pyver}
    virtualenv -p ${pyver} venv-${pyver}
    . venv-${pyver}/bin/activate
    if ! ${pyver} ./setup.py install ; then
        echo "Install failed"
        exit 1
    fi

    if ! ${pyver} ./run_tests.py ; then
        echo "Tests failed"
        ret=1
    fi
done

exit ${ret}
