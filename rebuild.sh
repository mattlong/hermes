#!/bin/bash

PACKAGE_NAME=hermes
rm -rf dist $PACKAGE_NAME.egg-info
python setup.py sdist upload
#pip uninstall $PACKAGE_NAME
#rm -rf ~/.virtualenvs/$PACKAGE_NAME-dev/build/$PACKAGE_NAME
#pip install $PACKAGE_NAME
