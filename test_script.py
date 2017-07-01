# encoding: utf-8
"""Tests for conda-merge"""

import io
import contextlib
import glob
import pytest

import conda_merge as cm


def test_merge_names():
    """Should leave only the last name"""
    names = ['a', None, 'b', 'c', None, '']
    assert cm.merge_names(names) == 'c'
    assert cm.merge_names([]) is None
    assert cm.merge_names([None, None]) is None


def test_channels():
    # simple
    assert cm.merge_channels([['a', 'b'], ['b', 'c']]) == ['a', 'b', 'c']
    # contained
    full = list('abcd')
    assert cm.merge_channels([['a', 'b'], ['c', 'd'], full]) == full
    # complex -- other options might be possible, so failing for no reason is possible
    in_channels = [['a', 'b', 'c'], ['x', 'c', 'd'], ['b', 'f', 'd']]
    possible_out = [list(x) for x in ('abfxcd', 'abxfcd', 'axbcfd', 'axbfcd')]
    assert cm.merge_channels(in_channels) in possible_out
    # empty
    assert cm.merge_channels([None]) == []


def test_dependencies():
    deps1 = ['a', 'b', 'c', 'd', {'pip': ['x', 'y', 'z']}]
    deps2 = ['b=2.0.*', 'e', {'pip': ['x==1.0.0', 'w']}]
    deps3 = ['f<3', 'a>=4']
    out = ['a', 'a>=4', 'b', 'b=2.0.*', 'c', 'd', 'e', 'f<3',
           {'pip': ['w', 'x', 'x==1.0.0', 'y', 'z']}]
    assert cm.merge_dependencies([deps1, deps2, deps3]) == out
    # handling simple duplicates
    assert cm.merge_dependencies([['a'], ['a']]) == ['a']


def test_main():
    """Test the main entry point for the script with real examples"""
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        argv = list(glob.glob('example/*environment.yml'))
        cm.main(cm.parse_args(argv))
    out.seek(0)
    assert out.read() == open('example/output.yml').read()
