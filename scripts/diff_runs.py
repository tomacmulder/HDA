import argparse, hashlib
from pathlib import Path

FILES = [
    "statements.jsonl","links.jsonl","threads.jsonl","canon.json",
    "claims_is.jsonl","time_modality.jsonl","evidential.jsonl",
    "scaffold.jsonl","ontology.jsonl","accuracy.jsonl","is.json"
]

def sha1(p: Path) -> str:
    h = hashlib.sha1()
    with open(p,"rb") as f:
        for chunk in iter(lambda: f.read(131072), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True, help="Run dir A (e.g., out\\runs\\2025-11-01_2000)")
    ap.add_argument("--b", required=True, help="Run dir B")
    args = ap.parse_args()
    A, B = Path(args.a), Path(args.b)

    print(f"Comparing:\n  A = {A}\n  B = {B}\n")
    print("{:<22} {:>10} {:>42}   {:>10} {:>42}".format("file","A bytes","A sha1","B bytes","B sha1"))
    print("-"*116)
    for fn in FILES:
        pa, pb = A/fn, B/fn
        if pa.exists(): sa, ha = pa.stat().st_size, sha1(pa)
        else:           sa, ha = 0, "-"
        if pb.exists(): sb, hb = pb.stat().st_size, sha1(pb)
        else:           sb, hb = 0, "-"
        print("{:<22} {:>10} {:>42}   {:>10} {:>42}".format(fn, sa, ha, sb, hb))

if __name__ == "__main__":
    main()
