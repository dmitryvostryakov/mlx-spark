"""Materialize ONE reviewed upstream source to a new directory. Never installs it."""
import argparse, json, re, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--allow-network',action='store_true')
    p.add_argument('--lock',type=Path,required=True)
    p.add_argument('--destination',type=Path,default=ROOT/'.cache/upstream/mlx')
    a=p.parse_args()
    if not a.allow_network:raise SystemExit('Network disabled; pass --allow-network only after source review.')
    lock=json.loads(a.lock.read_text())
    if lock.get('review_state')!='approved':raise SystemExit('Lock must be explicitly reviewed and marked approved with review evidence.')
    if not lock.get('review_evidence'):raise SystemExit('review_evidence is required; a status string alone is insufficient.')
    entry=lock['sources']['mlx'];sha=entry['revision']
    if entry['repository']!='ml-explore/mlx' or not re.fullmatch('[0-9a-f]{40}',sha):raise SystemExit('Unexpected repository or non-immutable revision')
    dest=a.destination.resolve()
    if dest.exists():raise SystemExit('Destination exists; refusing to reset or overwrite it')
    dest.mkdir(parents=True)
    base=['git','-c','core.hooksPath=/dev/null','-c','protocol.file.allow=never','-C',str(dest)]
    def run(*args):return subprocess.run(base+list(args),check=True,capture_output=True,text=True,timeout=300)
    run('init');run('remote','add','origin','https://github.com/ml-explore/mlx.git')
    run('fetch','--depth','1','origin',sha);run('checkout','--detach',sha)
    if run('rev-parse','HEAD').stdout.strip()!=sha:raise SystemExit('Fetched revision mismatch')
    print(f'Source only materialized at {dest}. NOT built, imported, installed, or repackaged.')
if __name__=='__main__':main()
