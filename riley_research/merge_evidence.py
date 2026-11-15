"""Merge local evidence stores by content hash for read-only analysis."""
import argparse

from .evidence import EvidenceStore


def merge(destination, sources):
    target = EvidenceStore(destination)
    known = {row["evidence_hash"] for row in target.list()}
    added = 0
    for path in sources:
        source = EvidenceStore(path)
        if not source.verify():
            raise ValueError(f"Evidence integrity check failed: {path}")
        for row in source.list():
            if row["evidence_hash"] in known:
                continue
            target.append(row)
            known.add(row["evidence_hash"])
            added += 1
    return added, target.verify()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("destination")
    parser.add_argument("sources", nargs="+")
    args = parser.parse_args()
    print(merge(args.destination, args.sources))


if __name__ == "__main__":
    main()
