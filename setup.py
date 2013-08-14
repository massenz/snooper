#!/usr/bin/env python

__author__ = 'Marco Massenzio (marco@rivermeadow.com)'


import os
import re
import setuptools


VERSION = '0.10'


def get_data_files(src_dir, dest_dir, exclude_re=None):
    """ Helper method for setup.py.

    This method takes in a source and destination directory
    and builds a list suitable for passing into the 'data_files' argument for the setup function.

    Note: The dest_dir should usually be prefixed with the package name (i.e. 'my_package/etc').
          Otherwise pkg_resources.get_* will not be able to find your file/resource.
    """
    if exclude_re:
        exclude_re = re.compile(exclude_re)
    data_files = []
    for src_root, _, files in os.walk(src_dir):
        dest_root = src_root.replace(src_dir, dest_dir, 1)
        dir_files = []
        for file_ in files:
            if exclude_re and exclude_re.match(file_):
                pass
            dir_files.append(os.path.join(src_root, file_))
        data_files.append((dest_root, dir_files))
    return data_files


def get_requirements(filename='requirements.txt'):
    requirements = []
    with open(filename) as reqs:
        for line in reqs.readlines():
            requirements.append(line.strip())
    return requirements


setuptools.setup(
    name='snooper',
    version=VERSION,
    package_dir={'': 'src'},
    packages=setuptools.find_packages('src', exclude=['*.test']),
    zip_safe=False,
    install_requires=get_requirements(),
    scripts=['scripts/snooper',
             'scripts/snooper-webui',
             'src/server.py',
             'src/snooper.py']
)
