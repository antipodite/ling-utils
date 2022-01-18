#! /usr/bin/env python3
"""
Extra utilities for working with Glottolog
© Isaac Stead, Jan 2022
"""
import csv
import re

from pathlib import Path
from argparse import ArgumentParser
from pickle import dump, load

from cldfcatalog import Config
from pyglottolog import Glottolog
from treelib import Tree
from tabulate import tabulate


CACHE_FILE = Path("~/.glottocache.pickle")


class GlottoCache:
    """Save loaded Glottolog languoids so we don't have to wait every time"""
    def __init__(self, path=CACHE_FILE):
        self.cachepath = path.expanduser()
        try:
            with open(self.cachepath, "rb") as cachefile:
                self.cache = load(cachefile)
        except FileNotFoundError:
            self.cache = {}

        cfg = Config.from_file()
        self.glottolog = Glottolog(cfg.get_clone("glottolog"))
        # So we know whether to save
        self.written = False

    def get(self, glottocode):
        if not glottocode:
            return None
        elif glottocode in self.cache:
            return self.cache[glottocode]
        else:
            lg = self.glottolog.languoid(glottocode)
            self.cache[glottocode] = lg
            self.written = True
            return lg

    def save(self):
        if self.written:
            with open(self.cachepath, "wb") as cachefile:
                dump(self.cache, cachefile)


def get_node_descendants(glottocache, code):
    """Depth-first traverse Glottolog subtree starting at `code` node"""
    result = []
    queue = [glottocache.get(code)]
    while queue:
        this = queue.pop()
        result.append(this.glottocode)
        queue.extend(this.children)
    return result


def list_glottocodes(glottocache, args):
    """List glottocodes within subtree(s) feature"""
    codes = args.glottocodes.split(",")
    descendants = []
    for code in codes:
        descendants.extend(get_node_descendants(glottocache, code))
    if args.format:
        out = ["\"{}\"".format(d) for d in descendants]
        print(", ".join(out))
    else:
        print(" ".join(descendants))


def attach_glottolog_data(glottocache, args):
    """Given a spreadsheet where a certain column contains glottocodes,
    attach additional specified data from Glottolog in new column or
    columns.
    Currently just does subgrouping data because that's what I need rn"""
    ftype = args.spreadsheet_in.suffixes[0]
    if ftype not in [".csv", ".tsv"]:
        raise TypeError("Files of type {} not supported".format(ftype))
    with open(args.spreadsheet_in, "r") as f:
        reader = csv.reader(f)
        rows = [row for row in reader]

    # Look for the column containing glottocodes
    sample = rows[2] # Assume header
    code_col = None
    for i, cell in enumerate(sample):
        if re.match("[a-z]{4}[0-9]{4}", cell):
            code_col = i
    if not code_col:
        raise RuntimeError("No glottocodes found in sheet {}".format(args.spreadsheet_in))

    # Attach subgrouping data from Glottolog in a new column after existing ones
    for row in rows[1:]: # Assume header again
        glottocode = row[code_col]
        if args.v:
            print(glottocode)
        if glottocode:
            languoid = glottocache.get(glottocode)
            class_str = ", ".join([lg.name for lg in languoid.ancestors])
            row.append(class_str)

    # Write modified CSV to specified filename
    with open(args.spreadsheet_out, "w") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerows(rows)

    
def run():
    """Command line interface for Glottolog utilities"""
    cfg = Config.from_file()
    glottolog = Glottolog(cfg.get_clone("glottolog"))
    parser = ArgumentParser("Extra Glottolog utilities")
    subparsers = parser.add_subparsers(dest="subcommand", help="Subcommand")

    #
    # List glottocodes functionality
    #
    list_parser = subparsers.add_parser(
        "list",
        help="Print a flat list of glottocodes descended from supplied glottocodes"
    )
    list_parser.add_argument("glottocodes", type=str)
    list_parser.add_argument(
        "--format",
        action="store_true",
        help="Print with string formatting for Python, SQL, R, etc."
    )
    list_parser.add_argument(
        "--leaves",
        action="store_true",
        help="Leaf nodes only"
    )

    #
    # CSV glottocode data attach functionality
    #
    lookup_parser = subparsers.add_parser(
        "attach",
        help="Attach Glottolog subgrouping info to a spreadsheet containing Glottocodes"
    )
    lookup_parser.add_argument("spreadsheet_in", type=Path)
    lookup_parser.add_argument("spreadsheet_out", type=Path)

    # Global args
    parser.add_argument("-v", action="store_true", help="Verbose output")

    # Do the stuff
    args = parser.parse_args()
    glottocache = GlottoCache()
    
    if args.subcommand == "list":
        list_glottocodes(glottocache, args)
    elif args.subcommand == "attach":
        attach_glottolog_data(glottocache, args)

    glottocache.save()
    
if __name__ == "__main__":
    run()

