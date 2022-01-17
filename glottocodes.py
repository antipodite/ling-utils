#! /usr/bin/env python3
"""
Get a flat list of glottocodes below a subtree node or nodes for use in e.g. SQL scripts, nexus files
Isaac Stead 2022
"""
from argparse import ArgumentParser
from cldfcatalog import Config
from pyglottolog import Glottolog
from treelib import Tree
from tabulate import tabulate


def get_node_descendants(glottolog, code):
    result = []
    queue = [glottolog.languoid(code)]
    while queue:
        this = queue.pop()
        result.append(this.glottocode)
        queue.extend(this.children)
    return result
        

def run():
    cfg = Config.from_file()
    glottolog = Glottolog(cfg.get_clone("glottolog"))

    parser = ArgumentParser("Extra utilities on top of Pyglottolog etc")
    subparsers = parser.add_subparsers(help="Subcommand")
    subtree_list = subparsers.add_parser(
        "list",
        help="Print a flat list of glottocodes descended from supplied glottocodes"
    )
    subtree_list.add_argument("glottocodes", type=str)
    subtree_list.add_argument(
        "--format",
        action="store_true",
        help="Print with string formatting for Python, SQL, R, etc."
    )
    subtree_list.set_defaults(subtree_list=True)
    args = parser.parse_args()

    if args.glottocodes:
        codes = args.glottocodes.split(",")
        descendants = []
        for code in codes:
            descendants.extend(get_node_descendants(glottolog, code))
        if args.format:
            out = ["\"{}\"".format(d) for d in descendants]
            print(", ".join(out))
        else:
            print(" ".join(descendants))

if __name__ == "__main__":
    run()

