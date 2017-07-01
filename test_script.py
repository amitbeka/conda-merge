# encoding: utf-8
"""Tests for conda-merge"""

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
    possible_out = [list(x) for x in ('abfxcd', 'abxfcd', 'axbcfd')]
    assert cm.merge_channels(in_channels) in possible_out
