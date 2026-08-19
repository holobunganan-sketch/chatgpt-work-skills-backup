from __future__ import annotations
from pathlib import Path
from PIL import Image
from .common import write_json

def crop_visuals(pages_dir, records, out_dir):
    pages_dir=Path(pages_dir); out_dir=Path(out_dir); out_dir.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for r in records:
        page_path=pages_dir/f"page_{int(r['page']):04d}.png"
        img=Image.open(page_path)
        w,h=img.size
        x0,y0,x1,y1=r['bbox']
        box=(round(x0*w),round(y0*h),round(x1*w),round(y1*h))
        if not (0<=box[0]<box[2]<=w and 0<=box[1]<box[3]<=h):
            raise ValueError(f"Invalid bbox for {r['id']}: {r['bbox']}")
        crop=img.crop(box)
        out=out_dir/f"{r['id']}.png"; crop.save(out)
        item=dict(r); item['asset']=str(out); item['pixel_box']=list(box); item['pixel_size']=list(crop.size)
        manifest.append(item)
    write_json(out_dir/'visual_manifest.json',manifest)
    return manifest
