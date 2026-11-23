#!/usr/bin/env python3
"""Run pinned InternVL3.5 with documented dynamic image tiles and greedy decoding.

Image preprocessing follows the model card's 448px aspect-ratio tiling, maximum
12 tiles plus a thumbnail, with ImageNet normalization.
https://huggingface.co/OpenGVLab/InternVL3_5-4B
"""
import argparse
import hashlib
import json
from pathlib import Path

import torch
from PIL import Image
from torchvision import transforms as T
from torchvision.transforms.functional import InterpolationMode
from transformers import AutoModel, AutoTokenizer
from run_vlm_hf import extract_json_object

CODE_HASHES={
    'configuration_intern_vit.py':'6530df52748e4f7766568825e1d11f55dfa6cc421990020a640c548dc6cd2646',
    'configuration_internvl_chat.py':'e9fdff47225fd380d940a4a2b6818b303fd2a5fdddf44fce0a75b05a4beb1539',
    'conversation.py':'b1b9f280e9cb9211e519e2b8071002b57cc742aadb2f49b05fa674ee3c7d83ee',
    'modeling_intern_vit.py':'a33ec11c517041c7fcbaaff3d736d846498468efaf4a64400a89d55132d5f638',
    'modeling_internvl_chat.py':'ec972dd3d1c7f5da06455034d5cfe54968a9555dff60804edee9a7fb5759db34',
}


def image_tiles(path, tile_size=448, max_tiles=12):
    with Image.open(path) as source:
        image=source.convert('RGB')
    width,height=image.size
    candidates=sorted({(w,h) for n in range(1,max_tiles+1) for w in range(1,n+1) for h in range(1,n+1) if 1<=w*h<=max_tiles},key=lambda p:(p[0]*p[1],p[0],p[1]))
    best=(1,1); difference=float('inf')
    for w,h in candidates:
        delta=abs(width/height-w/h)
        if delta<difference or (delta==difference and width*height>.5*tile_size**2*w*h):
            best=(w,h);difference=delta
    w,h=best
    resized=image.resize((tile_size*w,tile_size*h))
    tiles=[resized.crop((col*tile_size,row*tile_size,(col+1)*tile_size,(row+1)*tile_size)) for row in range(h) for col in range(w)]
    if len(tiles)>1: tiles.append(image.resize((tile_size,tile_size)))
    transform=T.Compose([T.Resize((tile_size,tile_size),interpolation=InterpolationMode.BICUBIC),T.ToTensor(),T.Normalize(mean=(.485,.456,.406),std=(.229,.224,.225))])
    return torch.stack([transform(tile) for tile in tiles]).to(device='cuda',dtype=torch.bfloat16)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--model',required=True);p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--limit',type=int)
    a=p.parse_args(); rows=[json.loads(s) for s in a.input.read_text().splitlines() if s.strip()]
    if a.limit is not None:rows=rows[:a.limit]
    if not rows or a.output.exists():raise ValueError('Empty input or output already exists')
    for name,digest in CODE_HASHES.items():
        if hashlib.sha256((Path(a.model)/name).read_bytes()).hexdigest()!=digest:
            raise ValueError(f'Pinned model code hash mismatch: {name}')
    tokenizer=AutoTokenizer.from_pretrained(a.model,trust_remote_code=True,use_fast=False,local_files_only=True)
    model=AutoModel.from_pretrained(a.model,torch_dtype=torch.bfloat16,low_cpu_mem_usage=True,use_flash_attn=False,trust_remote_code=True,local_files_only=True).eval().cuda()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:
        for row in rows:
            pixels=image_tiles(row['image']) if row.get('image') else None
            question=('<image>\n' if pixels is not None else '')+row['prompt']
            with torch.inference_mode():
                raw=model.chat(tokenizer,pixels,question,{'max_new_tokens':1024,'do_sample':False})
            parsed=extract_json_object(raw)
            out={'request_id':row['request_id'],'task':row['task'],'prompt_condition':row['prompt_condition'],'example_id':row['example_id'],'model_id':'internvl35_4b','checkpoint':a.model,'image_tiles':None if pixels is None else len(pixels),'parsed':parsed,'parse_valid':parsed is not None,'raw_response':raw}
            f.write(json.dumps(out,ensure_ascii=False)+'\n');f.flush()
            print(row['request_id'],'valid_json=',parsed is not None,'tiles=',out['image_tiles'],flush=True)


if __name__=='__main__':main()
