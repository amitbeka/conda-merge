conda-merge
===========

Tool for merging Conda (Anaconda) environment files into one file.
This is used to merge your application environment file with any other
environment file you might need (e.g. unit-tests, debugging, jupyter notebooks)
and create a consistent environment without breaking dependencies from the
previous environment files.

**Installation**:

::

    pip install conda-merge

**Usage**:

::

    conda-merge FILE1 FILE2 ... FILE-N > OUTPUT-FILE

A common problem with multiple environment files is that of pinned dependencies:
let's say ``environment.yml`` contains the dependency ``numpy=1.7``, and your
``dev-environment.yml`` contains ``pandas`` as a dependency. If you sequentially
apply the environment files (``conda env update -f environment.yml`` and then
``conda env update -f dev-environment.yml``) ``numpy`` will no longer be pinned
and will be upgraded to the latest version.

One option to solve it is by using the pinned dependencies file in the environment
directory, but this means storing your dependencies in another file which interacts
with ``environment.yml``, and makes the dependencies less clear to other users.
This script enables you to merge the two environment files and then run only
one ``conda env`` command to apply the change.
