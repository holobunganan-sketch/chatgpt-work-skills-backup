from __future__ import annotations
from pathlib import Path
from html import escape
import shutil
from .common import TOP_SECTIONS
import json


def _adapter_label(adapter_id):
    path=Path(__file__).resolve().parents[1]/'adapters'/f'{adapter_id}.json'
    if path.exists():
        try:
            return json.loads(path.read_text(encoding='utf-8')).get('label_zh',adapter_id)
        except Exception:
            return adapter_id
    return adapter_id

def _p(text, cls=None):
    c=f' class="{cls}"' if cls else ''
    return f'<p{c}>{escape(str(text))}</p>'

def _list(items):
    return '<ul>'+''.join(f'<li>{escape(str(x))}</li>' for x in items)+'</ul>'

def _source_label(pages):
    if not pages: return ''
    uniq=[]
    for x in pages:
        if x not in uniq: uniq.append(x)
    txt='、'.join(str(x) for x in uniq)
    return f'原文位置：第{txt}页'

def render_html(bundle, output_path, asset_source_dir=None):
    output=Path(output_path); output.parent.mkdir(parents=True,exist_ok=True)
    css_path=Path(__file__).resolve().parents[1]/'templates/kindle.css'
    css=css_path.read_text(encoding='utf-8')
    parts=['<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">',
           '<meta name="viewport" content="width=device-width, initial-scale=1">',
           f'<title>{escape(bundle.get("paper",{}).get("title_zh") or bundle.get("paper",{}).get("title_original","论文伴读"))}</title>',
           f'<style>{css}</style></head><body>']
    paper=bundle.get('paper',{})
    parts.append('<h2>论文题目</h2>')
    parts.append(f'<h1>{escape(paper.get("title_zh") or paper.get("title_original",""))}</h1>')
    if paper.get('title_original') and paper.get('title_original') != paper.get('title_zh'):
        parts.append(_p(paper['title_original'],'source'))

    o=bundle.get('orientation',{})
    parts.append('<h2>阅读前先建立框架</h2>')
    for label,key in [('文献的主导知识任务','dominant_task'),('这篇论文研究什么','topic'),('作者要回答什么问题','question'),('作者给出的核心回答','core_answer')]:
        parts.append(f'<h3>{label}</h3>'); parts.append(_p(o.get(key,'')))
    parts.append('<h3>全文阅读地图</h3>'); parts.append(_list(o.get('reading_map',[])))
    parts.append('<h3>阅读时需要注意什么</h3>'); parts.append(_list(o.get('watch_for',[])))

    parts.append('<h2>文献类型与阅读路线</h2>')
    primary_id=paper.get('primary_adapter','general-mixed')
    parts.append(_p(f"主适配器：{_adapter_label(primary_id)}"))
    if paper.get('secondary_adapters'): parts.append(_p('辅助适配器：'+'、'.join(_adapter_label(x) for x in paper['secondary_adapters'])))
    if paper.get('knowledge_tasks'): parts.append(_list(paper['knowledge_tasks']))

    sections={s['id']:s for s in bundle.get('source_sections',[])}
    summaries={s['source_section_id']:s['text'] for s in bundle.get('section_summaries',[])}
    units_by_sec={sid:[] for sid in sections}
    unassigned=[]
    for u in bundle.get('units',[]):
        if u.get('source_section_id') in units_by_sec: units_by_sec[u['source_section_id']].append(u)
        else: unassigned.append(u)
    visuals={v['id']:v for v in bundle.get('visuals',[])}

    parts.append('<h2>正文伴读</h2>')
    for sid,s in sections.items():
        parts.append(f'<h3>{escape(s.get("title_zh") or s.get("title_original") or "正文")}</h3>')
        for u in units_by_sec.get(sid,[]):
            parts.append(f'<h4>{escape(u.get("assistant_title",""))}</h4>')
            for para in u.get('translation_paragraphs',[]): parts.append(_p(para))
            if u.get('understanding_level') in ('brief','detailed') and (u.get('understanding_note') or '').strip():
                parts.append('<div class="note"><p><span class="label">理解提示：</span>'+escape(u['understanding_note'])+'</p></div>')
            for vid in u.get('visual_ids',[]):
                v=visuals.get(vid)
                if not v: continue
                parts.append('<div class="visual">')
                title=' '.join(x for x in [v.get('number',''),v.get('title_zh','')] if x)
                if title: parts.append(f'<p class="visual-title">{escape(title)}</p>')
                asset_rel=v.get('asset','')
                asset_name=Path(asset_rel).name if asset_rel else ''
                if asset_name:
                    dest_dir=output.parent/'assets'; dest_dir.mkdir(exist_ok=True)
                    if asset_source_dir:
                        src=Path(asset_source_dir)/asset_name
                    else:
                        src=Path(asset_rel)
                    if src.exists():
                        shutil.copy2(src,dest_dir/asset_name) if src.resolve()!=(dest_dir/asset_name).resolve() else None
                        parts.append(f'<img src="assets/{escape(asset_name)}" alt="{escape(title or vid)}">')
                parts.append('<p><span class="label">图表解读：</span>'+escape(v.get('interpretation',''))+'</p>')
                parts.append('</div>')
            source=_source_label(u.get('source_pages',[]))
            if source: parts.append(_p(source,'source'))
        if sid in summaries:
            parts.append('<div class="note"><p><span class="label">本节小结：</span>'+escape(summaries[sid])+'</p></div>')
    for u in unassigned:
        parts.append(f'<h4>{escape(u.get("assistant_title",""))}</h4>')
        for para in u.get('translation_paragraphs',[]): parts.append(_p(para))

    s=bundle.get('synthesis',{})
    parts.append('<h2>全文串联理解</h2>')
    for label,key in [('这篇论文讨论什么','topic'),('作者准备解决什么问题','problem'),('作者给出的核心回答','core_answer'),('作者怎样得出这个回答','how_answered'),('最重要的依据','key_evidence'),('论文中最需要谨慎理解的地方','caution'),('这篇论文贡献了什么','contribution'),('它没有解决什么','unresolved')]:
        parts.append(f'<h3>{label}</h3>'); parts.append(_p(s.get(key,'')))
    parts.append('<h3>整篇论文的逻辑链</h3><div class="logic-chain">')
    chain=s.get('logic_chain',[])
    for i,x in enumerate(chain):
        parts.append(_p((('→ ' if i else '')+str(x))))
    parts.append('</div>')

    parts.append('<h2>术语与符号说明</h2>')
    for g in bundle.get('glossary',[]):
        term=' / '.join(x for x in [g.get('term',''),g.get('translation','')] if x)
        parts.append(f'<h4>{escape(term)}</h4>'); parts.append(_p(g.get('explanation','')))
    parts.append('</body></html>')
    output.write_text(''.join(parts),encoding='utf-8')
    return output
