#! /usr/bin/env python3
"""Computing the mean edit distance between sets of reflexes for claimed "PPh" protoforms
© Isaac Stead February 2022

From my notes:
Hypothesis: if we have a cognate which is a recent borrowing rather
than an ancient cognate we should be able to see a difference in the
phonological variation between the reflexes. Less variation -> more
likely to be a recent borrowing, more variation -> less likely to be a
recent borrowing. Make a metric by calculating the mean disparity or
just Levenshtein distance within each cognate set This is complicated
somewhat by the fact that Philippine phonologies aren’t very different
from each other… this will be why Blust thinks that he can reconstruct
most of these to a hypothetical PPh. But it’s worth a try anyway. We
could compare the low disparity ones to Zorc’s lists of lexical items
for his different Philippine “axes”.

- Using Levenshtein distance as the metric initially, but this isn't
  necessarily that good as it has no concept of phonemes, but will do
  for a first pass
"""
from csv import DictReader
from collections import namedtuple, Counter
from itertools import product, accumulate
from pathlib import Path
from argparse import ArgumentParser
from re import split, sub, findall

from cldfcatalog import Config
from pyglottolog import Glottolog

from Levenshtein import distance
from tabulate import tabulate


def groupby(seq, access_fn):
    indices = {}
    for i, item in enumerate(seq):
        key = access_fn(item)
        if key in indices:
            indices[key].append(i)
        else:
            indices[key] = [i]
    return [ [seq[i] for i in idxs] for idxs in indices.values() ]


def chunk(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def rm_affixes(lexeme, return_all=False):
    """Very crude way to remove prefixes-, -postfixes, and <infixes> from an ACD form"""
    match = "^\S+-|-\S+$|<\S+>"
    root = sub(match, "", lexeme)
    affixes = findall(match, lexeme)
    if return_all:
        return root, matches
    else:
        return root


class CognateSet:
    def __init__(self, protoform, reflexes=[], glottocodes=[], gloss=None, affixes=False):
        self.protoform = protoform
        if affixes:
            self.reflexes = reflexes
        else:
            self.reflexes = [rm_affixes(r) for r in reflexes]
        self.glottocodes = glottocodes
        self.gloss = gloss

    @property
    def n_reflexes(self):
        return len(self.reflexes)

    def matrix(self, measure=distance):
        """Pairwise Levenshtein distance between reflexes for this ACD cognate set"""
        dists = [measure(a, b) for a, b in  product(self.reflexes, repeat=2)]
        matrix = chunk(dists, self.n_reflexes) # Chop into rows
        return matrix

    @property
    def mean_distance(self):
        """Mean pairwise Levenshtein distance"""
        flat = [d for subseq in self.matrix() for d in subseq]
        return sum(flat) / self.n_reflexes

    def table(self):
        """Display the distance matrix formatted as a table"""
        table = [ [r] + row for r, row in zip(self.reflexes, self.matrix()) ]
        return tabulate(table, headers=self.reflexes)

    def __str__(self):
        return "<{}> \"{}\" : {} reflexes".format(self.protoform, self.gloss, self.n_reflexes)


def load_reflex_data(fname, protolangs=False, affixes=False):
    """Expects sheet with at least Protoform | Reflex | Glottocode"""
    with open(fname) as f:
        rows = [row for row in DictReader(f)]
    cognatesets = []
    for group in groupby(rows, lambda r: r["ProtoForm"]):
        if not protolangs: # Filter out protolangs (row has no glottocode)
            group = [row for row in group if row["GlottoCode"]]
        cs = CognateSet(
            protoform = group[0]["ProtoForm"],
            reflexes = [row["Reflex"] for row in group],
            glottocodes = [row["GlottoCode"] for row in group],
            affixes=affixes
        )
        cognatesets.append(cs)
    return cognatesets


def run():
    # Glottolog setup
    cfg = Config.from_file()
    glottolog = Glottolog(cfg.get_clone("glottolog"))

    # Console interface
    parser = ArgumentParser("Cognate set disparity")
    parser.add_argument(
        "--sets",
        type=str,
        help="Protoform for cognate sets to display, separated by commas"
    )
    parser.add_argument(
        "--rm_affixes",
        action="store_false",
        help="Whether to attempt to remove morphological affixes from cognates"
    )
    parser.add_argument("sheet", type=Path, help="Path of input spreadsheet, in CSV format")
    args = parser.parse_args()

    cognatesets = load_reflex_data(args.sheet, affixes=args.rm_affixes)
    print("ACD Cognate disparity analysis v0: Found {} cognate sets".format(len(cognatesets)))
    if args.sets:
        protoforms = args.sets.split(",")
        for cs in cognatesets:
            if cs.protoform in protoforms:
                print("Cognate set: {}".format(cs))
                print(cs.table())


if __name__ == "__main__":
    run()
