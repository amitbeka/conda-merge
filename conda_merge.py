#! /usr/bin/python3
# encoding: utf-8
"""Tool to merge environment files of the conda package manager"""

import argparse
from collections import OrderedDict, deque
from copy import deepcopy
import sys

import yaml


class MergeError(Exception):
    pass


def main(args):
    env_definitions = [read_file(f) for f in args.files]
    unified_definition = {}
    name = merge_names(env.get('name') for env in env_definitions)
    if name:
        unified_definition['name'] = name
    channels = merge_channels(env.get('channels') for env in env_definitions)
    if channels:
        unified_definition['channels'] = channels
    deps = merge_dependencies(env.get('dependencies') for env in env_definitions)
    if deps:
        unified_definition['dependencies'] = deps
    yaml.dump(unified_definition, sys.stdout,
              indent=2, default_flow_style=False)



def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+')
    return parser.parse_args(argv)


def read_file(path):
    with open(path) as f:
        return yaml.load(f)


def merge_names(names):
    """Merge names of environments by leaving the last non-blank one"""
    actual_names = [name for name in names if name]
    if actual_names:
        return actual_names[-1]


def merge_channels(channels_list):
    dag = DAG()
    try:
        for channels in channels_list:
            if channels is None: # not found in this environment definition
                continue
            for i, channel in enumerate(channels):
                dag.add_node(channel)
                if i > 0:
                    dag.add_edge(channels[i-1], channel)
    except ValueError as exc:
        raise MergeError("Can't satisfy priority {}".format(exc.msg))
    return dag.topological_sort()


def merge_dependencies(deps_list):
    only_pips = []
    unified_deps = []
    for deps in deps_list:
        if deps is None: # not found in this environment definition
            continue
        for dep in deps:
            if isinstance(dep, dict) and dep['pip']:
                only_pips.append(dep['pip'])
            elif dep not in unified_deps:
                unified_deps.append(dep)
    unified_deps = sorted(unified_deps)
    if only_pips:
        unified_deps.append(merge_pips(only_pips))
    return unified_deps


def merge_pips(pip_list):
    return {'pip': sorted(req for reqs in pip_list for req in reqs)}


class DAG(object):
    """Directed acyclic graph for merging channel priorities.

    This is a stripped down version adopted from:
    https://github.com/thieman/py-dag

    """

    def __init__(self):
        self.graph = OrderedDict()

    def __len__(self):
        return len(self.graph)

    def add_node(self, node_name):
        if node_name not in self.graph:
            self.graph[node_name] = set()

    def add_edge(self, from_node, to_node):
        if from_node not in self.graph or to_node not in self.graph:
            raise KeyError('one or more nodes do not exist in graph')
        test_graph = deepcopy(self.graph)
        test_graph[from_node].add(to_node)
        if self.validate():
            self.graph[from_node].add(to_node)
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


if __name__ == '__main__':
    main(parse_args())
