#!/usr/bin/env python3
"""Draw a connection diagram for dumped data"""
#

import collections
import glob
import re


def read_ids(f):
    this = None
    refs = set()

    matcher = re.compile("(.*) ([-a-z]+-[0-9a-f]{17})$")

    while True:
        line = f.readline()
        if line == '':
            break

        line = line.strip()
        
        if line.startswith("resourceid: "):
            this = line.split()[1]
            continue

        match = matcher.match(line)

        if not match:
            continue


        if match[1] == "Description:":
            continue

        refs.add(match[2])

    if this is None:
        print("# Could not find this id")
        return

    for ref in refs:
        if ref == this:
            continue
        print(f' "{this}" -> "{ref}"')


def main():
    db = {}

    print("digraph G {")
    print(" node [ shape = rectangle ]")
    print(" rankdir = LR")

    for filename in glob.glob("**/*.yaml", recursive=True):
        with open(filename, "r+") as f:
            read_ids(f)
    
    print("}")


if __name__ == "__main__":
    main()
