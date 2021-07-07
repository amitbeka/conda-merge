"""A setup module for conda-merge"""

import os
from setuptools import setup
from codecs import open

here = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file
with open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='conda-merge',
    version='0.2.0',

    description='Tool for merging conda environment files',
    long_description=long_description,

    url='https://github.com/amitbeka/conda-merge',
    author='Amit Beka',
    author_email='amit.beka@gmail.com',

    license='MIT',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Build Tools',
        'Topic :: System :: Installation/Setup',
    ],

    keywords='conda anaconda environment',

    py_modules=["conda_merge"],

    install_requires=['pyyaml'],
    python_requires='>=3',
    extras_require={
        'test': ['pytest'],
    },

    entry_points={
        'console_scripts': [
            'conda-merge=conda_merge:main',
        ],
    },
)
