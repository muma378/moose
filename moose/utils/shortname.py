# -*- coding: utf-8 -*-
from .treelib import Node, Tree

class Trie(Tree):
    pass


def shorten(names):
    for name in names:
        pass


def build_trie(strings_list):
    tree = Tree()
    for string in strings_list:
        sub_tree = tree
        for char in string:
            new_node = Node(identifier=char)
            if sub_tree.contains(new_node):
                # if already exists
                node = tree.get_node(new_node)
            else:
                node = tree.add_node(new_node)
            sub_tree = sub_tree.subtree(node)
    return tree
