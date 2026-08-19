from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from scripts.ingest_pdf import ingest_pdf
from scripts.crop_visuals import crop_visuals
from scripts.validate_bundle import validate_bundle
from scripts.render_html import render_html
from scripts.common import read_json, write_json

def load_paragraphs(path):
    return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]

def cmd_prepare(args):
    meta=ingest_pdf(args.pdf,args.out,args.dpi)
    print(json.dumps(meta,ensure_ascii=False,indent=2))

def cmd_crop(args):
    records=read_json(args.bboxes)
    result=crop_visuals(Path(args.session)/'source/pages',records,Path(args.session)/'output/assets')
    print(json.dumps(result,ensure_ascii=False,indent=2))

def cmd_validate(args):
    session=Path(args.session)
    bundle=read_json(args.bundle or session/'work/paper_bundle.json')
    pars=load_paragraphs(session/'source/paragraphs.jsonl')
    report=validate_bundle(bundle,pars)
    write_json(session/'validation/report.json',report)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    raise SystemExit(0 if report['valid'] else 2)

def cmd_render(args):
    session=Path(args.session)
    bundle=read_json(args.bundle or session/'work/paper_bundle.json')
    pars=load_paragraphs(session/'source/paragraphs.jsonl')
    report=validate_bundle(bundle,pars)
    write_json(session/'validation/report.json',report)
    if not report['valid'] and not args.force:
        print(json.dumps(report,ensure_ascii=False,indent=2),file=sys.stderr); raise SystemExit(2)
    out=Path(args.out) if args.out else session/'output/paper_reader_kindle.html'
    render_html(bundle,out,asset_source_dir=session/'output/assets')
    print(str(out))


def cmd_init_work(args):
    s=Path(args.session); work=s/'work'; work.mkdir(parents=True,exist_ok=True)
    classification={
      'primary_adapter':'general-mixed','secondary_adapters':[],'knowledge_tasks':[],
      'confidence':0.0,'reasoning_summary':''
    }
    unit_plan={'schema_version':'2.0','units':[]}
    bundle={
      'schema_version':'2.0',
      'paper':{'title_original':'','title_zh':'','primary_adapter':'general-mixed','secondary_adapters':[],'knowledge_tasks':[]},
      'orientation':{'dominant_task':'','topic':'','question':'','core_answer':'','reading_map':[],'watch_for':[]},
      'seven_elements':{'topic':'','problem':'','core_claim':'','evidence':'','reasoning':'','uncertainty':'','contribution':''},
      'source_sections':[],'units':[],'visuals':[],'section_summaries':[],
      'synthesis':{'topic':'','problem':'','core_answer':'','how_answered':'','key_evidence':'','caution':'','contribution':'','unresolved':'','logic_chain':[]},
      'glossary':[]
    }
    for name,obj in [('classification.json',classification),('unit_plan.json',unit_plan),('paper_bundle.json',bundle)]:
        path=work/name
        if not path.exists(): write_json(path,obj)
    print(str(work))

def cmd_status(args):
    s=Path(args.session)
    data={
      'prepared':(s/'source/document.json').exists(),
      'classification':(s/'work/classification.json').exists(),
      'unit_plan':(s/'work/unit_plan.json').exists(),
      'bundle':(s/'work/paper_bundle.json').exists(),
      'validation':(s/'validation/report.json').exists(),
      'rendered':(s/'output/paper_reader_kindle.html').exists()
    }
    print(json.dumps(data,ensure_ascii=False,indent=2))

def main(argv=None):
    p=argparse.ArgumentParser(description='中文学术文献深度伴读 v2.0 runtime')
    sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('prepare',help='解析PDF并生成段落/页面/图表候选'); a.add_argument('pdf'); a.add_argument('--out',required=True); a.add_argument('--dpi',type=int,default=144); a.set_defaults(func=cmd_prepare)
    a=sub.add_parser('init-work',help='创建固定结构的work模板'); a.add_argument('session'); a.set_defaults(func=cmd_init_work)
    a=sub.add_parser('crop-visuals',help='按规范化bbox原样裁切图表'); a.add_argument('session'); a.add_argument('--bboxes',required=True); a.set_defaults(func=cmd_crop)
    a=sub.add_parser('validate',help='验证结构化伴读数据'); a.add_argument('session'); a.add_argument('--bundle'); a.set_defaults(func=cmd_validate)
    a=sub.add_parser('render',help='确定性生成Kindle HTML'); a.add_argument('session'); a.add_argument('--bundle'); a.add_argument('--out'); a.add_argument('--force',action='store_true'); a.set_defaults(func=cmd_render)
    a=sub.add_parser('status',help='查看session处理状态'); a.add_argument('session'); a.set_defaults(func=cmd_status)
    args=p.parse_args(argv); args.func(args)
if __name__=='__main__': main()
