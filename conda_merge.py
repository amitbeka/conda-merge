#!/usr/bin/python3
# encoding: utf-8
"""Tool to merge environment files of the conda package manager.

Given a list of environment files, print a unified environment file.
Usage: conda-merge file1 file2 ... [> unified-environment]

Merge strategy for each part of the definition:
  name: keep the last name, if any is given (according to the order of the files).
  channels: merge the channel priorities of all files and keep each file's priorities
    in the same order. If there is a collision between files, report an error.
  dependencies: merge the dependencies and remove duplicates, sorts alphabetically.
    conda itself can handle cases like [numpy, numpy=1.7] gracefully so no need
    to do that. You may beautify the dependencies by hand if you wish.
    The script also doesn't detect collisions, relying on conda to point that out.

"""


import argparse
from collections import OrderedDict, deque
from copy import deepcopy
import sys
import re

import yaml


__version__ = '0.2.0'


class MergeError(Exception):
    """Errors during conda-merge run, mainly failing to merge channels/dependencies"""
    pass


def merge_envs(args):
    """Main script entry point.

    `args` is a Namescpace object, `args.files` should be a list of file paths
    to merge.
    No return value, the unified yaml file is printed to stdout.
    If an error occurs, a message is printed to stderr and exception is raised.

    """
    env_definitions = [read_file(f) for f in args.files]
    unified_definition = {}
    name = merge_names(env.get('name') for env in env_definitions)
    if name:
        unified_definition['name'] = name
    try:
        channels = merge_channels(env.get('channels') for env in env_definitions)
    except MergeError as exc:
        print("Falied to merge channel priorities.\n{}\n".format(exc.args[0]),
              file=sys.stderr)
        raise
    if channels:
        unified_definition['channels'] = channels
    deps = merge_dependencies(
        [env.get('dependencies') for env in env_definitions], remove_builds=args.remove_builds
    )
    if deps:
        unified_definition['dependencies'] = deps
    # dump the unified environment definition to stdout
    yaml.dump(unified_definition, sys.stdout,
              indent=2, default_flow_style=False)


def parse_args(argv=None):
    """Parse command line arguments (or user provided ones as list)"""
    description = sys.modules[__name__].__doc__
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('files', nargs='+')
    parser.add_argument(
        "--remove-builds",
        action="store_true",
        help="Remove build specifiers from dependencies (ignores then for merging purposes)",
    )
    return parser.parse_args(argv)


def read_file(path):
    with open(path) as f:
        return yaml.safe_load(f)


def merge_names(names):
    """Merge names of environments by leaving the last non-blank one"""
    actual_names = [name for name in names if name]
    if actual_names:
        return actual_names[-1]


def merge_channels(channels_list):
    """Merge multiple channel priorities list and output a unified one.

    Use a directed-acyclic graph to create a topological sort of the priorities,
    so that the order from each environment file will be preserved in the output.
    If this cannot be satisfied, a MergeError is raised.
    If no channel priories are found (all are None), return an emply list.

    """
    dag = DAG()
    try:
        for channels in channels_list:
            if channels is None:  # not found in this environment definition
                continue
            for i, channel in enumerate(channels):
                dag.add_node(channel)
                if i > 0:
                    dag.add_edge(channels[i-1], channel)
        return dag.topological_sort()
    except ValueError as exc:
        raise MergeError("Can't satisfy channels priority: {}".format(exc.args[0]))


def merge_dependencies(deps_list, remove_builds=False):
    """Merge all dependencies to one list and return it.

    Two overlapping dependencies (e.g. package-a and package-a=1.0.0) are not
    unified, and both are left in the list (except cases of exactly the same
    dependency). Conda itself handles that very well so no need to do this ourselves,
    unless you want to prettify the output by hand.

    """
    only_pips = []
    unified_deps = []
    for deps in deps_list:
        if deps is None:  # not found in this environment definition
            continue
        for dep in deps:
            if isinstance(dep, dict) and dep['pip']:
                only_pips.append(dep['pip'])
            else:
                if remove_builds:
                    dep = _remove_build(dep)
                if dep not in unified_deps:
                    unified_deps.append(dep)
    unified_deps = sorted(unified_deps)
    if only_pips:
        unified_deps.append(merge_pips(only_pips))
    return unified_deps


def merge_pips(pip_list):
    """Merge pip requirements lists the same way as `merge_dependencies` work"""
    return {'pip': sorted({req for reqs in pip_list for req in reqs})}


def _remove_build(dep):
    """Remove build version if exists, return dep"""
    m = re.match(r"([^=]+=[^=]+)=([^=]+)$", dep, re.IGNORECASE)
    return m.group(1) if m else dep


class DAG(object):
    """Directed acyclic graph for merging channel priorities.

    This is a stripped down version adopted from:
    https://github.com/thieman/py-dag (MIT license)

    """

    def __init__(self):
        self.graph = OrderedDict()

    def __len__(self):
        return len(self.graph)

    def add_node(self, node_name):
        if node_name not in self.graph:
            self.graph[node_name] = []

    def add_edge(self, from_node, to_node):
        if from_node not in self.graph or to_node not in self.graph:
            raise KeyError('one or more nodes do not exist in graph')
        if to_node not in self.graph[from_node]:
            test_graph = deepcopy(self.graph)
            test_graph[from_node].append(to_node)
            if self.validate():
                self.graph[from_node].append(to_node)
            else:
                raise ValueError("{} -> {}".format(from_node, to_node))

    @property
    def independent_nodes(self):
        """Return a list of all nodes in the graph with no dependencies."""
        dependent_nodes = set(node for dependents in self.graph.values()
                              for node in dependents)
        return [node for node in self.graph.keys()
                if node not in dependent_nodes]

    def validate(self):
        """Return whether the graph doesn't contain a cycle"""
        if len(self.independent_nodes) > 0:
            try:
                self.topological_sort()
                return True
            except ValueError:
                return False
        return False

    def topological_sort(self):
        """Return a topological ordering of the DAG.

        Raise an error if this is not possible (graph is not valid).

        """
        in_degree = {}
        for node in self.graph:
            in_degree[node] = 0

        for from_node in self.graph:
            for to_node in self.graph[from_node]:
                in_degree[to_node] += 1

        queue = deque()
        for node in in_degree:
            if in_degree[node] == 0:
                queue.appendleft(node)

        sorted_nodes = []
        while queue:
            independent_node = queue.pop()
            sorted_nodes.append(independent_node)
            for next_node in self.graph[independent_node]:
                in_degree[next_node] -= 1
                if in_degree[next_node] == 0:
                    queue.appendleft(next_node)

        if len(sorted_nodes) == len(self.graph):
            return sorted_nodes
        else:
            raise ValueError('graph is not acyclic')


def main():
    """Main entry point for console_scripts of setup.py"""
    try:
        merge_envs(parse_args())
    except MergeError:
        return 1


if __name__ == '__main__':
    main()
