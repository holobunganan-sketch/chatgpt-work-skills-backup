from __future__ import annotations
import argparse,shutil
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description='Install zh-academic-paper-reader skill')
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--target',choices=['agents','codex','claude'])
    g.add_argument('--path')
    a=p.parse_args()
    home=Path.home()
    base=Path(a.path).expanduser() if a.path else {'agents':home/'.agents/skills','codex':home/'.codex/skills','claude':home/'.claude/skills'}[a.target]
    dest=base/'zh-academic-paper-reader'; dest.parent.mkdir(parents=True,exist_ok=True)
    src=Path(__file__).resolve().parent
    if dest.exists(): shutil.rmtree(dest)
    ignore=shutil.ignore_patterns('.git','__pycache__','.pytest_cache','tests','*.pyc','docs')
    shutil.copytree(src,dest,ignore=ignore)
    print(dest)
if __name__=='__main__': main()
