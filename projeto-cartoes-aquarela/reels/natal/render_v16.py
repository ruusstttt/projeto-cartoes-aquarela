"""Reel de Natal no estilo da referência 2.mp4, com a montagem em papel da V15."""

from functools import lru_cache
import math
import os
import re

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

import render_v15 as paper
from trilha import compor

S = paper.S
W, H = S
work = paper.work
materials = paper.inputs
LANCZOS = Image.Resampling.LANCZOS
CREAM = (247, 240, 222)
PINE = (35, 70, 52)
WINE = (128, 53, 53)
HONEY = (219, 186, 113)
sequence = paper.motion


@lru_cache(32)
def hand(size, weight=500):
    font = ImageFont.truetype(str(materials / "Caveat.ttf"), size)
    font.set_variation_by_axes([weight])
    return font


def texture(base, seed, vignette):
    rng = np.random.default_rng(seed)
    yy, xx = np.ogrid[-1:1:complex(H), -1:1:complex(W)]
    cloud = Image.fromarray(rng.integers(32, 214, (53, 32), dtype=np.uint8)).resize(S, Image.Resampling.BICUBIC)
    grain = rng.normal(0, 1.55, (H, W)) + (np.asarray(cloud).astype(float)-128) * .019
    grain -= vignette * ((xx + .18)**2 + (yy + .2)**2)
    return Image.fromarray(np.clip(np.array(base) + grain[:,:,None], 0, 255).astype('uint8')).convert("RGBA")


forest = texture((40, 78, 57), 712, 4.8)
cream = texture(CREAM, 38, .65)
cloth = ImageOps.fit(paper.photo(materials / "xadrez-vinho.jpeg"), (W, 565), LANCZOS, centering=(.5,.57)).convert("RGBA")
stage = forest.copy()
stage.alpha_composite(cloth, (0, 1400))
santa = paper.card_img(paper.photo(materials / "papai-noel.png"), 479)
deer = paper.card_img(paper.rena, 462)
detail = ImageOps.fit(paper.photo(materials / "interior-arvore.jpeg"), (W,1094), LANCZOS, centering=(.55,.71)).convert("RGBA")
collection = ImageOps.fit(paper.photo(materials / "colecao-na-mesa.jpg"), (W,817), LANCZOS, centering=(.52,.58)).convert("RGBA")
portrait = ImageOps.fit(paper.photo(paper.repo/"retrato-profissional-raynara.png"), (606,761), LANCZOS, centering=(.5,.29)).convert("RGBA")


def text(im, xy, string, size, color, weight=500, anchor="ls"):
    ImageDraw.Draw(im).text(xy,string,font=hand(size,weight),fill=color,anchor=anchor)


def twinkle(im, x, y, r, pose):
    radii = [.78,.87,.98,1.05,1.01,.92,.83,.76,.74,.74]
    r *= radii[pose % len(radii)]
    pts=[(x,y-r),(x+r*.20,y-r*.22),(x+r*.66,y),(x+r*.17,y+r*.22),(x,y+r),(x-r*.18,y+r*.20),(x-r*.69,y),(x-r*.16,y-r*.23)]
    d=ImageDraw.Draw(im)
    d.polygon(pts,fill=HONEY)
    d.polygon([(x,y-r),(x,y),(x-r*.69,y),(x-r*.16,y-r*.23)],fill=(242,216,151))


def letters(im, string, center, baseline, size, color, pose, *, weight=540, distance=22):
    """Letters land separately. Use the intact script word for the reading hold."""
    font=hand(size,weight)
    left=center-font.getlength(string)/2
    if pose >= len(string)+4:
        text(im,(left,baseline),string,size,color,weight)
        return
    for i,ch in enumerate(string):
        offset=sequence([distance,round(distance*.62),round(distance*.22),-2,0],pose-i)
        x=left+font.getlength(string[:i])
        if ch!=" ":
            text(im,(x,baseline+offset),ch,size,color,weight)


def cover(k):
    im=stage.copy()
    settle=sequence([0,.16,.36,.59,.77,.91,1.02,1.05,1.02,1],k)
    paper.paste(im,deer,(733+47*(1-settle),1208+75*(1-settle)),-12+5*(1-settle),1,.95)
    paper.paste(im,santa,(367-47*(1-settle),1180+67*(1-settle)),8-6*(1-settle),1,1.1)
    letters(im,"Cartões de",535,409,169,CREAM,k+6,weight=480,distance=10)
    letters(im,"Natal",517,719,360,CREAM,k,weight=520,distance=32)
    twinkle(im,151,542,24,k//2)
    twinkle(im,907,416,12,k//2+5)
    text(im,(525,1680),"em aquarela",68,CREAM,530,"ms")
    return im


def envelope_scene(k):
    im=stage.copy()
    twinkle(im,164,605,26,k//2)
    twinkle(im,879,540,37,k//2+4)
    idx=min(36,max(0,k-2))
    if idx <= 24:
        paper.envelope(im)
        sheet=Image.new("RGBA",S)
        paper.paste(sheet,paper.insert,(533,paper.positions[idx]+paper.insert.height/2),0,1,.62)
        im.alpha_composite(sheet.crop((0,0,W,paper.LIP)),(0,0))
    else:
        dy=sequence([0,14,46,101,191,321,482,674,889,1105,1265,1300],idx-25)
        paper.envelope(im,dy)
        paper.paste(im,paper.insert,(533,390+paper.insert.height/2),0,1,.62)
    return im


def note_caption(im, y, age):
    im.alpha_composite(cream,(0,y))
    d=ImageDraw.Draw(im)
    d.line((0,y+1,W,y+1),fill=(143,67,59),width=7)
    text(im,(98,y+143),"Com as suas palavras,",54,WINE,540)
    if age >= 0:
        text(im,(92,y+313+sequence([16,7,2,0],age)),"o seu Natal",133,PINE,520)
    if age >= 3:
        text(im,(91,y+458+sequence([18,9,3,0],age-3)),"um pouco mais único",105,WINE,540)
    if age >= 9:
        end=sequence([0,55,130,191,228],age-9)
        d.line([(98,y+507),(98+end,y+502)],fill=(178,142,77),width=4)


def note_scene(k):
    im=stage.copy()
    turns=[0,-3,-7,-4,4,17,36,58,79,96,119,144,163,176,183,180]
    travels=[0,0,.018,.045,.079,.12,.171,.229,.296,.371,.45,.529,.612,.695,.774,.843,.901,.95,.981,1]
    t=sequence(travels,k)
    angle=sequence(turns,k)
    obj,ox,oy=paper.tilted_card(angle,t)
    scale=1-.04*t
    cx=533+6*t
    cy=(390+paper.insert.height/2)*(1-t)+616*t-53*math.sin(math.pi*t)
    paper.paste(im,obj,(cx+(ox+obj.width/2)*scale,cy+(oy+obj.height/2)*scale),-1.8*t,scale,.62+.45*math.sin(math.pi*t))
    twinkle(im,164,605,26,k//2)
    twinkle(im,904,460,30,k//2+3)
    if k>=8:
        y=sequence([1919,1795,1580,1370,1221,1142,1103,1091,1094],k-8)
        note_caption(im,y,k-15)
    return im


def interior_scene(k):
    im=cream.copy()
    im.alpha_composite(detail,(0,0))
    note_caption(im,1094,30)
    return im


def heading(im):
    text(im,(91,963),"Escolha o seu",92,PINE,510)
    text(im,(87,1076),"cartão de Natal.",117,WINE,540)


def offer(k):
    im=cream.copy()
    im.alpha_composite(collection,(0,0))
    d=ImageDraw.Draw(im)
    d.line((0,814,W,814),fill=WINE,width=7)
    heading(im)
    if k>=2:
        n=k-2
        letters(im,"20",153,1201,113,WINE,n,weight=690,distance=42)
        text(im,(234,1193+sequence([14,6,1,0],n)),"unidades de abertura",74,PINE,560)
    d.line((95,1240,948,1240),fill=(180,165,129),width=2)
    for j,(x,label,price) in enumerate([(95,"1 cartão","35"),(537,"3 cartões","99")]):
        n=k-6-3*j
        if n<0:
            continue
        shift=sequence([52,31,12,-2,0],n)*(-1 if j==0 else 1)
        text(im,(x+shift,1319),label,65,PINE,510)
        text(im,(x+shift,1434),"R$",78,WINE,530)
        letters(im,price,x+shift+159,1439,121,WINE,n,weight=680,distance=30)
    d.line((95,1480,948,1480),fill=(180,165,129),width=2)
    if k>=12:
        y=sequence([18,10,4,-1,0],k-12)
        text(im,(92,1578+y),"Pedidos no direct",82,PINE,610)
        text(im,(95,1660+y),"Envie a palavra NATAL",64,WINE,550)
    return im


mount=paper.wheat((657,937),CREAM,73)


def artist(k):
    im=forest.copy()
    im.alpha_composite(cloth,(0,1460))
    x=sequence([85,47,19,4,-2,0],k)
    ang=sequence([-4.4,-3.4,-2.4,-1.5,-1,-1.3],k)
    sheet=mount.copy()
    sheet.alpha_composite(portrait,(25,24))
    letters(sheet,"Raynara",326,887,120,WINE,max(0,k-3),weight=540,distance=20)
    paper.paste(im,sheet,(531+x,911+round(x*.42)),ang,1,1)
    twinkle(im,174,500,26,k//2)
    twinkle(im,876,1107,32,k//2+3)
    return im


def dissolve(previous, current, k, length):
    if k>=length:
        return current
    t=(k+1)/(length+1)
    t=t*t*(3-2*t)
    return Image.blend(previous,current,t)


def sequence_to_disk(fn,frames,prefix,previous=None,fade=3):
    for i in range(frames):
        im=fn(i)
        if previous is not None and i<fade:
            im=dissolve(previous,im,i,fade)
        im.convert("RGB").save(work/f"{prefix}-{i:03d}.jpg",quality=96,subsampling=0)


def render():
    # Five 10-pose/s scenes surround real 30 fps painting footage.
    video=materials/"pintura-v16.mp4"
    for time,stem in [(0,"brush-first"),(5.96,"brush-last")]:
        paper.run("-y","-ss",time,"-i",video,"-frames:v",1,"-update",1,work/f"{stem}.png")
    first=paper.photo(work/"brush-first.png").convert("RGBA")
    last=paper.photo(work/"brush-last.png").convert("RGBA")
    def opening(k):
        frame=cover(k)
        return dissolve(frame,first,k-32,3) if k>=32 else frame
    sequence_to_disk(opening,35,"cover")
    sequence_to_disk(envelope_scene,41,"env",last,3)
    sequence_to_disk(note_scene,43,"note")
    sequence_to_disk(interior_scene,21,"inside",note_scene(42),3)
    sequence_to_disk(offer,61,"offer",interior_scene(20),3)
    sequence_to_disk(artist,25,"artist",offer(60),4)
    compor(work/"trilha.wav",28.6,extended=True)
    args=[]
    names=["cover","brush","env","note","inside","offer","artist"]
    pipes=[]
    for i,name in enumerate(names):
        if name=="brush":
            args.extend(["-i",video])
            norm="scale=1080:1920:in_color_matrix=bt709:out_color_matrix=bt709:out_range=tv"
        else:
            args.extend(["-framerate",10,"-start_number",0,"-i",work/f"{name}-%03d.jpg"])
            norm="scale=1080:1920:out_color_matrix=bt709:out_range=tv"
        pipes.append(f"[{i}:v]{norm},setsar=1,fps=30,format=yuv420p,setpts=PTS-STARTPTS[v{i}]")
    pipes.append("".join(f"[v{i}]" for i in range(len(names)))+"concat=n=7:v=1:a=0[v]")
    out=work/"reel-cartoes-de-natal-v16.mp4"
    paper.run("-y",*args,"-i",work/"trilha.wav","-filter_complex_threads",3,"-filter_complex",";".join(pipes),
              "-map","[v]","-map","7:a","-map_metadata","-1","-c:v","libx264","-preset","veryfast","-threads",5,
              "-crf",16,"-colorspace","bt709","-color_trc","bt709","-color_primaries","bt709","-color_range","tv",
              "-af","loudnorm=I=-17:TP=-1.5:LRA=8,aresample=48000","-c:a","aac","-b:a","224k",
              "-movflags","+faststart+write_colr","-t","28.6",out)
    info=paper.run("-i",out,"-f","null","-")
    assert re.search(r"frame=\s*858\b",info) and "Duration: 00:00:28.60" in info
    assert re.search(r"Video: h264.*1080x1920.*30 fps",info) and "Audio: aac" in info
    os.replace(out,paper.build/out.name)


if __name__=="__main__":
    render()
