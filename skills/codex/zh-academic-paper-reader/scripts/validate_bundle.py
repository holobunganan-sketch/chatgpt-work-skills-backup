from __future__ import annotations
import re
from collections import Counter
from .common import ADAPTER_IDS

NUM_RE=re.compile(r'(?<!\w)\d+(?:\.\d+)?%?')
PROTOCOL_RESULT_RE=re.compile(r'(结果显示|结果表明|研究发现|显著改善|显著降低|significantly improved|results showed)',re.I)

def _issue(code,msg,where=None):
    d={'code':code,'message':msg}
    if where is not None: d['where']=where
    return d

def validate_bundle(bundle, source_paragraphs):
    errors=[]; warnings=[]
    required_top=['schema_version','paper','orientation','seven_elements','source_sections','units','visuals','synthesis','glossary']
    missing_top=[k for k in required_top if k not in bundle]
    if missing_top:
        errors.append(_issue('TOP_LEVEL_FIELD_MISSING',f'Missing top-level fields: {missing_top}'))
    primary=bundle.get('paper',{}).get('primary_adapter')
    secondary=bundle.get('paper',{}).get('secondary_adapters',[])
    for a in [primary,*secondary]:
        if a not in ADAPTER_IDS: errors.append(_issue('UNKNOWN_ADAPTER',f'Unknown adapter: {a}'))

    eligible=[p['id'] for p in source_paragraphs if not p.get('excluded_reason')]
    mapping=[]
    unit_by_pid={}
    for u in bundle.get('units',[]):
        ids=u.get('source_paragraph_ids',[]); mapping.extend(ids)
        for pid in ids: unit_by_pid[pid]=u
    c=Counter(mapping)
    for pid in eligible:
        if c[pid]==0: errors.append(_issue('SOURCE_PARAGRAPH_MISSING',f'{pid} is not mapped',pid))
        elif c[pid]>1: errors.append(_issue('SOURCE_PARAGRAPH_DUPLICATED',f'{pid} mapped {c[pid]} times',pid))
    extra=[pid for pid in mapping if pid not in set(eligible)]
    if extra: warnings.append(_issue('EXCLUDED_SOURCE_MAPPED',f'Excluded/unknown paragraphs mapped: {sorted(set(extra))}'))

    src={p['id']:p.get('text','') for p in source_paragraphs}
    for u in bundle.get('units',[]):
        original=' '.join(src.get(pid,'') for pid in u.get('source_paragraph_ids',[]))
        trans=' '.join(u.get('translation_paragraphs',[]))
        nums=set(NUM_RE.findall(original)); tnums=set(NUM_RE.findall(trans))
        missing=sorted(nums-tnums)
        if missing:
            warnings.append(_issue('NUMERIC_TOKEN_MISMATCH',f"Numbers absent from translation: {', '.join(missing)}",u.get('id')))
        if u.get('understanding_level') in ('brief','detailed') and not (u.get('understanding_note') or '').strip():
            errors.append(_issue('UNDERSTANDING_NOTE_MISSING','understanding_level requires note',u.get('id')))

    visuals=bundle.get('visuals',[])
    vids=[v.get('id') for v in visuals]
    for vid,count in Counter(vids).items():
        if count>1: errors.append(_issue('VISUAL_DUPLICATED',f'Visual {vid} appears {count} times'))
    visual_set=set(vids)
    for v in visuals:
        if not (v.get('interpretation') or '').strip(): errors.append(_issue('VISUAL_INTERPRETATION_MISSING','Visual requires exactly one interpretation',v.get('id')))
        if not (v.get('asset') or '').strip(): errors.append(_issue('VISUAL_ASSET_MISSING','Visual requires original crop asset',v.get('id')))
    visual_refs=[]
    for u in bundle.get('units',[]):
        visual_refs.extend(u.get('visual_ids',[]))
        unknown=set(u.get('visual_ids',[]))-visual_set
        if unknown: errors.append(_issue('UNIT_UNKNOWN_VISUAL',f'Unknown visuals: {sorted(unknown)}',u.get('id')))
    for vid,count in Counter(visual_refs).items():
        if count>1: errors.append(_issue('VISUAL_REFERENCED_MULTIPLE_UNITS',f'Visual {vid} is referenced by {count} units',vid))

    if primary=='protocol':
        texts=[]
        syn=bundle.get('synthesis',{})
        texts += [str(syn.get(k,'')) for k in ('core_answer','key_evidence','how_answered')]
        texts += [' '.join(u.get('translation_paragraphs',[])) for u in bundle.get('units',[]) if '结果或发现' in u.get('rhetorical_functions',[])]
        if PROTOCOL_RESULT_RE.search(' '.join(texts)):
            errors.append(_issue('PROTOCOL_RESULT_CLAIM','Protocol bundle contains result-like generated claim'))

    units=bundle.get('units',[])
    if len(units)>=4:
        singleton=sum(1 for u in units if len(u.get('source_paragraph_ids',[]))==1)
        if singleton/len(units)>0.6:
            warnings.append(_issue('EXCESSIVE_SINGLETON_UNITS','Most cognitive units contain only one source paragraph; inspect for mechanical fragmentation'))
    for u in units:
        chars=sum(len(x) for x in u.get('translation_paragraphs',[]))
        if chars>1800: warnings.append(_issue('UNIT_TOO_LONG',f'{chars} Chinese characters in one unit',u.get('id')))

    coverage={'eligible':len(eligible),'mapped_once':sum(1 for pid in eligible if c[pid]==1),'ratio':(sum(1 for pid in eligible if c[pid]==1)/len(eligible) if eligible else 1.0)}
    return {'errors':errors,'warnings':warnings,'coverage':coverage,'valid':not errors}
