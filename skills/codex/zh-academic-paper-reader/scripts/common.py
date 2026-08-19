from __future__ import annotations
from pathlib import Path
import json

ADAPTER_IDS = {
    'empirical-imrad','systematic-review-meta','scoping-review','narrative-integrative-critical-review',
    'conceptual-theoretical','methods-technical-algorithm','qualitative','humanities-interpretive-historical',
    'case-report-case-study-process','guideline-consensus-policy','formal-proof-math-logic','protocol','dataset-resource','general-mixed'
}

TOP_SECTIONS = ['论文题目','阅读前先建立框架','文献类型与阅读路线','正文伴读','全文串联理解','术语与符号说明']

def read_json(path: str|Path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def write_json(path: str|Path, data):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
