from __future__ import annotations
from pathlib import Path
import json,re
import fitz
from .common import write_json

CAPTION_RE=re.compile(r'^\s*((?:Figure|Fig\.?|Table)\s*[A-Za-z]?\d+[A-Za-z]?)\b',re.I)
REF_RE=re.compile(r'^\s*(References|Bibliography|Literature cited|参考文献)\s*$',re.I)
HEADING_RE=re.compile(r'^\s*(Abstract|Introduction|Background|Methods?|Materials? and Methods?|Results?|Discussion|Conclusions?|References|Bibliography)\s*$',re.I)

def _clean(text:str)->str:
    return re.sub(r'\s+',' ',text).strip()

def ingest_pdf(pdf_path, session_dir, dpi=144):
    pdf_path=Path(pdf_path); session=Path(session_dir)
    source=session/'source'; pages_dir=source/'pages'; pages_dir.mkdir(parents=True,exist_ok=True)
    doc=fitz.open(pdf_path)
    pars=[]; candidates=[]; page_manifest=[]; pid=1; references_mode=False; first_content_heading_seen=False
    scale=dpi/72.0
    for pageno,page in enumerate(doc, start=1):
        pix=page.get_pixmap(matrix=fitz.Matrix(scale,scale), alpha=False)
        pix.save(pages_dir/f'page_{pageno:04d}.png')
        blocks=page.get_text('blocks', sort=True)
        raw_page_text=' '.join(_clean(b[4]) for b in blocks if len(b)>=5 and _clean(b[4]))
        page_manifest.append({'page':pageno,'image':f'pages/page_{pageno:04d}.png','text_char_count':len(raw_page_text),'needs_visual_transcription':len(raw_page_text)<40})
        for block in blocks:
            if len(block)<5: continue
            x0,y0,x1,y1,text=block[:5]
            text=_clean(text)
            if not text: continue
            m=CAPTION_RE.match(text)
            if REF_RE.match(text): references_mode=True
            excl=None
            if m:
                excl='visual_caption'
            elif references_mode:
                excl='references'
            elif pageno==1 and not first_content_heading_seen:
                if HEADING_RE.match(text) and not REF_RE.match(text):
                    first_content_heading_seen=True
                elif pid>1:
                    # probable author/affiliation/front matter before first section
                    excl='front_matter'
            rec={'id':f'p{pid:04d}','page':pageno,'bbox':[x0,y0,x1,y1],'text':text,'excluded_reason':excl}
            pars.append(rec); pid+=1
            if m:
                candidates.append({'id':f'vc{len(candidates)+1:03d}','page':pageno,'label':m.group(1),'caption':text,'caption_bbox':[x0,y0,x1,y1],'status':'needs_bbox'})
    doc_meta={'source_file':pdf_path.name,'page_count':len(doc),'paragraph_count':len(pars),'visual_candidate_count':len(candidates),'dpi':dpi}
    doc.close()
    write_json(source/'document.json',doc_meta)
    with (source/'paragraphs.jsonl').open('w',encoding='utf-8') as f:
        for p in pars: f.write(json.dumps(p,ensure_ascii=False)+'\n')
    write_json(source/'visual_candidates.json',candidates)
    write_json(source/'page_manifest.json',page_manifest)
    return doc_meta
