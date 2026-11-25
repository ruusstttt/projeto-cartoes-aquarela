"""Render the 204 stop-motion poses and export the Christmas reel."""

from pathlib import Path
from functools import lru_cache
import math
import os
import re
import shutil
import subprocess
import tempfile
from trilha import compor

import numpy as np
from PIL import (
    Image,
    ImageChops,
    ImageDraw,
    ImageEnhance,
    ImageFilter,
    ImageFont,
    ImageOps,
)

here = Path(__file__).resolve().parent
inputs = here / "materiais"
repo = here.parents[1] / "assets"
fonts = Path(
    os.environ.get(
        "BOOKMAN_DIR", Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    )
)
ff = os.environ.get("FFMPEG") or shutil.which("ffmpeg")
if not ff:
    raise SystemExit("Instale o FFmpeg ou indique o executável na variável FFMPEG.")
build = here / "build"
build.mkdir(exist_ok=True)
temp = tempfile.TemporaryDirectory(dir=build)
work = Path(temp.name)


def run(*args):
    p = subprocess.run(
        [str(ff), "-hide_banner", "-nostdin", *map(str, args)],
        cwd=work,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if p.returncode:
        raise RuntimeError(p.stdout[-4000:])
    return p.stdout


def photo(path):
    with Image.open(path) as im:
        return ImageOps.exif_transpose(im).convert("RGB")


W, H = 1080, 1920
S = (W, H)
ivory = (246, 236, 215)


def wheat(sz, tint=ivory, seed=1):
    w, h = sz
    r = np.random.default_rng(seed)
    noise = r.normal(0, 1.6, (h, w)).astype(np.float32)
    clouds = (
        Image.fromarray(
            r.integers(90, 160, (max(3, h // 36), max(3, w // 36)), dtype=np.uint8)
        )
        .resize(sz, Image.Resampling.BICUBIC)
        .filter(ImageFilter.GaussianBlur(9))
    )
    noise += (np.asarray(clouds, dtype=np.float32) - 125) * 0.055
    arr = np.clip(np.array(tint, dtype=np.float32) + noise[:, :, None], 0, 255).astype(
        "uint8"
    )
    im = Image.fromarray(arr).convert("RGBA")
    mask = Image.new("L", sz)
    top = [(x, int(r.integers(1, 5))) for x in range(1, w, 9)]
    bottom = [(x, h - int(r.integers(1, 6))) for x in range(w - 1, 0, -8)]
    ImageDraw.Draw(mask).polygon(
        [(1, 3)] + top + [(w - 2, 2), (w - 1, h - 4)] + bottom + [(1, h - 2)], fill=255
    )
    im.putalpha(mask)
    return im


def paste(dst, asset, xy, rot=0, scale=1, shadow=1):
    if scale != 1:
        asset = asset.resize(
            (max(1, round(asset.width * scale)), max(1, round(asset.height * scale))),
            Image.Resampling.LANCZOS,
        )
    if rot:
        asset = asset.rotate(rot, Image.Resampling.BICUBIC, expand=True)
    x, y = round(xy[0] - asset.width / 2), round(xy[1] - asset.height / 2)
    if shadow:
        border = 20
        ma = Image.new("L", (asset.width + 40, asset.height + 40))
        ma.paste(asset.getchannel("A"), (border, border))
        ma = ma.filter(ImageFilter.GaussianBlur(6 * shadow)).point(
            lambda t: round(t * 0.38)
        )
        sh = Image.new("RGBA", ma.size, (26, 23, 14, 0))
        sh.putalpha(ma)
        dst.alpha_composite(
            sh, (x - border + round(5 * shadow), y - border + round(10 * shadow))
        )
    dst.alpha_composite(asset, (x, y))


INK = (38, 57, 45)
RED = (142, 48, 49)
GOLD = (158, 111, 54)
PAPER = (250, 244, 228)


@lru_cache(None)
def book(size, style="reg"):
    return ImageFont.truetype(
        str(
            fonts
            / {
                "reg": "BOOKOS.TTF",
                "italic": "BOOKOSI.TTF",
                "bold": "BOOKOSB.TTF",
                "bolditalic": "BOOKOSBI.TTF",
            }[style]
        ),
        size,
    )


@lru_cache(None)
def sans(size):
    face = ImageFont.truetype(str(inputs / "PlusJakartaSans.ttf"), size)
    face.set_variation_by_axes([680])
    return face


def tracked(d, x, y, st, face, gap, color):
    for ch in st:
        d.text((x, y), ch, font=face, fill=color, anchor="ls")
        x += face.getlength(ch) + gap


def motion(seq, k):
    return seq[min(len(seq) - 1, max(0, k))]


# Original two-colour watercolor check. Adjacent bands are separate pigment washes.
def table():
    yy, xx = np.ogrid[:H, :W]
    rr = np.random.default_rng(24)
    waves = rr.integers(0, 255, (32, 18), dtype=np.uint8)
    light = (
        np.asarray(
            Image.fromarray(waves).resize(S, Image.Resampling.BICUBIC), dtype=np.float32
        )
        / 255
        - 0.5
    )
    noise = rr.normal(0, 1, (H, W)).astype(np.float32)
    arr = np.zeros((H, W, 3), dtype=np.float32) + [233, 225, 203]

    def stroke(coord, where, width, col, alpha):
        dist = np.abs((coord - where + period / 2) % period - period / 2)
        edge = np.clip((width / 2 - dist + 1 + light * 2 + noise * 0.32) / 2.5, 0, 1)
        strength = (alpha * (1 + light * 0.16 + noise * 0.025) * edge)[..., None]
        arr[:] = arr * (1 - strength) + np.array(col) * strength

    period = 274
    for p, phase in [
        (
            xx + 2.3 * np.sin(yy / 147) + 1.4 * np.sin(yy / 60) + 0.7 * np.cos(yy / 29),
            43,
        ),
        (yy + 2 * np.sin(xx / 158) + 1.1 * np.cos(xx / 56) + 0.8 * np.sin(xx / 23), 94),
    ]:
        stroke(p, phase, 63, (101, 126, 90), 0.35)
        stroke(p, phase - 28, 9, (120, 136, 88), 0.13)
        stroke(p, phase + 96, 9, (143, 63, 56), 0.52)
        stroke(p, phase + 120, 2.8, (150, 103, 68), 0.34)
    arr += (
        light * 6 + noise * 2.2 + 1.5 * np.sin(2.12 * xx) + 1.0 * np.cos(2.05 * yy)
    )[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype("uint8")).convert("RGBA")


ground = table()
# Use the photographed upper-right ink star of the real reindeer card.
rena = photo(inputs / "rena.png")
region = rena.crop((745, 386, 1028, 700))
arr = np.asarray(region.convert("RGB"), dtype=float)
maxink = np.maximum(255 - arr[:, :, 2], 255 - arr[:, :, 0])
mask = Image.new("L", region.size)
ImageDraw.Draw(mask).polygon(
    [
        (114, 0),
        (140, 0),
        (156, 118),
        (203, 75),
        (215, 73),
        (171, 134),
        (282, 134),
        (282, 157),
        (163, 166),
        (215, 220),
        (208, 227),
        (151, 182),
        (159, 314),
        (132, 314),
        (126, 181),
        (72, 226),
        (66, 223),
        (112, 161),
        (0, 171),
        (0, 147),
        (110, 138),
        (59, 92),
        (65, 81),
        (123, 122),
    ],
    fill=255,
)
alpha = np.clip((maxink - 12) / 200, 0, 1) * (np.asarray(mask) / 255)
star = Image.new("RGBA", region.size)
rgba = np.zeros((region.height, region.width, 4), dtype=np.uint8)
rgba[:, :, :3] = np.clip(
    np.stack([175 - maxink * 0.30, 124 - maxink * 0.22, 56 - maxink * 0.12], axis=-1),
    0,
    255,
)
rgba[:, :, 3] = (alpha * 255).astype("uint8")
star = Image.fromarray(rgba)


@lru_cache(192)
def stamped_star(size, angle):
    # A faceted gold centre catches the light, while the outer points retain her brushwork.
    foil = Image.new("RGBA", star.size)
    pen = ImageDraw.Draw(foil)
    cx, cy = 139, 153
    for j, r in enumerate([122, 73, 128, 62, 131, 71, 117, 72]):
        phi = math.radians(-92 + j * 45)
        ux, uy = math.cos(phi), math.sin(phi)
        vx, vy = -uy, ux
        tip = (cx + r * ux, cy + r * uy)
        a = (cx + vx * 9, cy + vy * 9)
        b = (cx - vx * 9, cy - vy * 9)
        pen.polygon([(cx, cy), a, tip], fill=(149, 94, 41, 222))
        pen.polygon([(cx, cy), b, tip], fill=(213, 169, 83, 235))
    foil.alpha_composite(star)
    return foil.resize((size, round(size * 1.1)), Image.Resampling.LANCZOS).rotate(
        angle, Image.Resampling.BICUBIC, expand=True
    )


def sparkle(im, k, coords):
    for j, (x, y, size) in enumerate(coords):
        cycle = (k + 7 * j) % 22
        fac = motion([0.62, 0.76, 0.94, 1.07, 1.07, 1, 0.90, 0.82, 0.74, 0.68], cycle)
        asset = stamped_star(round(size * fac), [0, 14, -19, 7][j % 4])
        paste(im, asset, (x, y), 0, 1, 0)


def card_img(im, width, height=None):
    if height is None:
        height = round(width * im.height / im.width)
    return im.resize((width, height), Image.Resampling.LANCZOS).convert("RGBA")


# Correct the perspective of the entire photographed card, from edge to edge.
photo_back = photo(inputs / "versos.png")
dest = [(0, 0), (600, 0), (600, 770), (0, 770)]
src = [(590, 68), (1001, 21), (1146, 546), (664, 612)]
M = []
pv = []
for (x, y), (u, v) in zip(dest, src):
    M.extend([[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]])
    pv.extend([u, v])
coef = np.linalg.solve(M, pv)
reverse = photo_back.transform(
    (600, 770), Image.Transform.PERSPECTIVE, coef, Image.Resampling.BICUBIC
).convert("RGBA")
# Lift the photographed paper by the same neutral gain across the whole sheet.
reverse = (
    ImageEnhance.Brightness(reverse)
    .enhance(1.075)
    .resize((698, 896), Image.Resampling.LANCZOS)
)
env_raw = photo(inputs / "envelope.jpg").crop((115, 710, 953, 1650))
rgb = np.asarray(env_raw, dtype=float)
m = np.clip((rgb[:, :, 0] - rgb[:, :, 1] - 4) / 15, 0, 1)
env = env_raw.convert("RGBA")
env.putalpha(Image.fromarray(np.uint8(m * 255)).filter(ImageFilter.MedianFilter(3)))


def envelope(im, dy=0):
    paste(im, env, (115 + env.width / 2, 710 + env.height / 2 + dy), 0, 1, 0.85)


headpaper = wheat((805, 276), PAPER, 23)
headback = wheat((811, 276), RED, 24)
subpaper = wheat((864, 242), PAPER, 31)
portrait = ImageOps.fit(
    photo(repo / "retrato-profissional-raynara.png"),
    (646, 790),
    Image.Resampling.LANCZOS,
    centering=(0.5, 0.32),
).convert("RGBA")
tape = wheat((170, 55), (193, 183, 141), 64)
for x in range(12, tape.width, 15):
    ImageDraw.Draw(tape).line([(x, 7), (x - 6, 46)], fill=(204, 194, 156), width=2)
tape.putalpha(tape.getchannel("A").point(lambda p: round(p * 0.88)))
LIP = 1143
# This card is taller than the pocket. It starts partly visible, sized so its
# hidden bottom edge fits inside the actual kraft envelope.
insert = card_img(photo(inputs / "papai-noel.png"), 518)
tops = [
    968,
    968,
    962,
    949,
    928,
    903,
    872,
    837,
    798,
    756,
    710,
    663,
    617,
    571,
    531,
    495,
    463,
    438,
    418,
    403,
    394,
    390,
]


def pull_pose(im, k):
    envelope(im)
    cardlayer = Image.new("RGBA", S)
    top = motion(tops, k)
    paste(cardlayer, insert, (533, top + insert.height / 2), 0, 1, 0.62)
    # The pocket occludes the entire sheet and its shadow below the opening,
    # including the area below the bottom of the envelope.
    im.alpha_composite(cardlayer.crop((0, 0, W, LIP)), (0, 0))


@lru_cache(1)
def loaded_envelope():
    im = ground.copy()
    pull_pose(im, 0)
    return im


deer_offer = card_img(rena, 529)


# Draw ink on movable paper elements at printer resolution.
@lru_cache(320)
def glyph(ch, size, style, color):
    face = book(size, style)
    a, b, c, d = face.getbbox(ch, anchor="ls")
    im = Image.new("RGBA", (c - a + 12, d - b + 12))
    ImageDraw.Draw(im).text((6 - a, 6 - b), ch, font=face, fill=color, anchor="ls")
    return im, (a - 6, b - 6)


def baseline_letters(im, string, x, y, size, style, color, k, delays):
    f = book(size, style)
    for i, ch in enumerate(string):
        age = k - delays[i]
        if age < 0 or ch == " ":
            continue
        obj, (ox, oy) = glyph(ch, size, style, color)
        sign = 1 if i % 3 == 0 else -1
        dy = motion([-46, -23, 5, -2, 0], age)
        dx = motion([12, 7, -3, 1, 0], age) * sign
        rot = motion([18, 9, -4, 1, 0], age) * sign
        left = x + f.getlength(string[:i]) + ox
        paste(
            im,
            obj,
            (left + obj.width / 2 + dx, y + oy + obj.height / 2 + dy),
            rot,
            1,
            0,
        )


def prepare_brush():
    for j, rate in enumerate([7, 8]):
        run(
            "-y",
            "-i",
            inputs / f"pintura-{j}.mp4",
            "-map",
            "0:v:0",
            "-vf",
            f"fps={rate},scale=1080:1920:out_color_matrix=bt709:out_range=pc",
            "-start_number",
            0,
            "-q:v",
            2,
            work / f"paint{j}-%02d.jpg",
        )


def intro15(k):
    j = 0 if k < 15 else 1
    ix = k if j == 0 else min(11, k - 15)
    frame = photo(work / f"paint{j}-{ix:02d}.jpg").convert("RGBA")
    if k < 19:
        slip = headpaper.copy()
        d = ImageDraw.Draw(slip)
        tracked(d, 48, 57, "CARTÕES EM AQUARELA", sans(26), 3, RED)
        baseline_letters(slip, "Natal", 43, 170, 123, "bold", INK, k, [0, 1, 1, 2, 3])
        baseline_letters(
            slip,
            "feito à mão",
            50,
            245,
            66,
            "italic",
            RED,
            k,
            [3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 7],
        )
        for i, (x, y, sz) in enumerate([(674, 96, 90), (742, 64, 48)]):
            age = k - 3 * i
            if age >= 0:
                paste(
                    slip,
                    stamped_star(sz, 0),
                    (x, y),
                    motion([30, 17, 4, -2, 0], age),
                    motion([0.3, 0.6, 0.93, 1.05, 1], age),
                    0,
                )
        x = motion([0, -18, -84, -236, -540, -1050], k - 14)
        paste(frame, headback, (488 + x, 398), 2, 1, 0.7)
        paste(frame, slip, (476 + x, 385), 1, 1, 0.9)
    if k >= 24:
        # The cut switches from the brush tip to the first pose of the envelope.
        opacity = motion([0.08, 0.27, 0.59, 0.86], k - 24)
        return Image.blend(frame, loaded_envelope(), opacity)
    return frame


# The artwork slides behind the real pocket lip, using hand-set exposure positions.
positions = [
    968,
    968,
    962,
    953,
    939,
    921,
    895,
    865,
    832,
    796,
    758,
    718,
    678,
    638,
    599,
    563,
    528,
    498,
    470,
    445,
    423,
    408,
    397,
    390,
    390,
]


def santa15(k):
    im = ground.copy()
    sparkle(im, k, [(176, 633, 104), (865, 483, 128), (934, 559, 56), (177, 1492, 73)])
    if k <= 24:
        envelope(im)
        sheet = Image.new("RGBA", S)
        paste(sheet, insert, (533, positions[k] + insert.height / 2), 0, 1, 0.62)
        im.alpha_composite(sheet.crop((0, 0, W, LIP)), (0, 0))
    else:
        dy = motion([0, 14, 46, 101, 191, 321, 482, 674, 889, 1105, 1265, 1300], k - 25)
        envelope(im, dy)
        paste(im, insert, (533, 390 + insert.height / 2), 0, 1, 0.62)
    return im


# Photograph-like perspective around the vertical axis with unmirrored artwork
# on each visible face. A detached shadow gives each tipped pose real depth.
def tilted_card(angle, progress):
    w = insert.width + (reverse.width - insert.width) * progress
    h = insert.height + (reverse.height - insert.height) * progress
    theta = math.radians(angle)
    plane = []
    for x, y in [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]:
        t = 1380 / (1380 + x * math.sin(theta))
        plane.append((x * math.cos(theta) * t, y * t))
    if angle > 90:
        plane = [plane[i] for i in (1, 0, 3, 2)]
    x0 = math.floor(min(x for x, y in plane)) - 2
    y0 = math.floor(min(y for x, y in plane)) - 2
    size = (
        math.ceil(max(x for x, y in plane) - x0) + 2,
        math.ceil(max(y for x, y in plane) - y0) + 2,
    )
    ref = insert if angle < 90 else reverse
    corners = [(0, 0), (ref.width, 0), (ref.width, ref.height), (0, ref.height)]
    mat = []
    vals = []
    for (xx, yy), (u, v) in zip(plane, corners):
        x, y = xx - x0, yy - y0
        mat.extend(
            [[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]]
        )
        vals.extend([u, v])
    ratio = abs(math.sin(theta))
    # Small neutral shift as the paper rotates away from the light.
    tex = ImageEnhance.Brightness(ref).enhance(1 - 0.14 * ratio)
    obj = tex.transform(
        size,
        Image.Transform.PERSPECTIVE,
        np.linalg.solve(mat, vals),
        Image.Resampling.BICUBIC,
    )
    return obj, x0, y0


def note_scene(im, k, shift=0):
    turning = [0, 0, -4, -9, -6, 5, 21, 41, 66, 82, 102, 126, 149, 166, 177, 183, 180]
    travel = [
        0,
        0,
        0,
        0.016,
        0.036,
        0.061,
        0.096,
        0.139,
        0.192,
        0.255,
        0.326,
        0.41,
        0.50,
        0.592,
        0.68,
        0.761,
        0.832,
        0.890,
        0.936,
        0.971,
        0.993,
        1,
    ]
    t = motion(travel, k)
    theta = motion(turning, k)
    if k < 22:
        obj, ox, oy = tilted_card(theta, t)
        lift = math.sin(t * math.pi)
        angle = 2 * t
        cx = 533 + 12 * t - 21 * lift + shift
        cy = (390 + insert.height / 2) * (1 - t) + 1050 * t - 64 * lift
        paste(
            im,
            obj,
            (cx + ox + obj.width / 2, cy + oy + obj.height / 2),
            angle,
            1,
            0.62 + 1.0 * lift + 0.3 * t,
        )
    else:
        paste(im, reverse, (545 + shift, 1050), 2, 1, 0.92)
    if k >= 12:
        age = k - 12
        slip = message15(min(28, age))
        dy = motion([-470, -290, -142, -52, -8, 3, 0], age)
        paste(
            im,
            slip,
            (532 + shift, 439 + dy),
            motion([4.5, 3, 2, 1, -0.1, -0.9, -0.7], age),
            1,
            0.95,
        )


@lru_cache(32)
def message15(age):
    im = subpaper.copy()
    baseline_letters(
        im,
        "o seu Natal",
        61,
        98,
        72,
        "bold",
        INK,
        age,
        [2, 2, 3, 3, 4, 4, 5, 6, 7, 8, 9],
    )
    line = "um pouco mais único"
    delays = [8 + (i // 2) for i in range(len(line))]
    baseline_letters(im, line, 60, 192, 72, "italic", RED, age, delays)
    if age >= 7:
        n = age - 7
        paste(
            im,
            stamped_star(76, -5),
            (767, 66),
            motion([30, 22, 10, -4, 0], n),
            motion([0.23, 0.60, 0.94, 1.08, 1], n),
            0,
        )
    return im


def note15(k):
    im = ground.copy()
    sparkle(
        im, k + 36, [(111, 892, 110), (907, 694, 138), (961, 768, 66), (208, 1469, 71)]
    )
    note_scene(im, k)
    return im


pinepaper = wheat((850, 181), (40, 71, 54), 712)
seedgold = (249, 226, 174)


@lru_cache(10)
def number_tile(ch):
    paper = wheat((91, 109), (249, 237, 205), 88 + ord(ch))
    d = ImageDraw.Draw(paper)
    d.text((45, 86), ch, font=book(85, "bold"), anchor="ms", fill=RED)
    return paper


@lru_cache(32)
def edition(age):
    paper = pinepaper.copy()
    d = ImageDraw.Draw(paper)
    for i, (ch, xc) in enumerate([("2", 144), ("0", 239)]):
        p = age - i
        if p < 0:
            continue
        sgn = [-1, 1][i]
        dx = motion([114, 73, 36, 13, -4, 0], p) * sgn
        dy = motion([-68, -49, -28, -9, 4, 0], p)
        angle = sgn * motion([29, 20, 10, 5, -2, 1.8], p)
        paste(paper, number_tile(ch), (xc + dx, 88 + dy), angle, 1, 0.38)
    if age >= 5:
        a = age - 5
        d.text(
            (312, 91 + motion([-10, -3, 2, 0], a)),
            "unidades",
            font=book(83, "bold"),
            fill=PAPER,
            anchor="ls",
        )
        if a >= 2:
            d.text(
                (317, 148 + motion([8, -2, 0], a - 2)),
                "de abertura",
                font=book(49, "italic"),
                fill=seedgold,
                anchor="ls",
            )
    return paper


@lru_cache(2)
def label_base(idx):
    im = wheat((407, 175), (249, 241, 222) if idx == 0 else (247, 237, 215), 400 + idx)
    d = ImageDraw.Draw(im)
    d.line((32, 70, 372, 70), fill=(197, 175, 132), width=2)
    d.text(
        (31, 53), ["1 cartão", "3 cartões"][idx], font=sans(38), fill=INK, anchor="ls"
    )
    return im


@lru_cache(40)
def label_price(idx, age):
    im = label_base(idx).copy()
    if age >= 0:
        num = ["35", "99"][idx]
        for j, ch in enumerate(num):
            obj, (ox, oy) = glyph(ch, 91, "bold", RED)
            x = (137, 194)[j]
            sign = [-1, 1][j]
            dx = sign * motion([29, 14, 3, -2, 0], age)
            dy = motion([-27, -17, -5, 3, 0], age)
            paste(
                im,
                obj,
                (x + ox + obj.width / 2 + dx, 151 + oy + obj.height / 2 + dy),
                sign * motion([14, 8, 3, -2, 0], age),
                1,
                0,
            )
        if age >= 3:
            ImageDraw.Draw(im).text(
                (32, 145), "R$", font=book(58, "reg"), fill=RED, anchor="ls"
            )
    return im


request_slip = wheat((850, 100), PAPER, 654)
qdraw = ImageDraw.Draw(request_slip)
qdraw.text((34, 65), "Pedidos no direct", font=sans(45), fill=INK, anchor="ls")
qdraw.text((808, 65), "Envie NATAL", font=book(42, "italic"), fill=RED, anchor="rs")
qdraw.line((492, 24, 492, 78), fill=(183, 157, 113), width=2)


def sale_parts(im, k, shift=0):
    # Reindeer makes a small arc, with an overshoot when the sheet meets the table.
    x = motion([1200, 1140, 977, 730, 465, 258, 114, 42, 1, -14, -7, 2, 0], k)
    y = motion([160, 110, 38, -39, -89, -105, -85, -58, -26, -3, 6, -2, 0], k)
    theta = motion([-17, -17, -16, -13, -10, -6, -2, 2.5, 4.2, 1, -2.9, -2, -2.2], k)
    paste(im, deer_offer, (523 + shift + x, 613 + y), theta, 1, 0.92)
    if k >= 6:
        n = k - 6
        off = motion([990, 765, 505, 293, 138, 49, 6, -5, 0], n)
        paste(
            im,
            edition(min(23, n - 4)) if n >= 4 else pinepaper,
            (523 + shift - off, 1062),
            motion([5, 4, 2.8, 1.8, 1, 0.3, -0.4, 0.2, 0.4], n),
            1,
            0.83,
        )
    for j, delay in enumerate([18, 24]):
        if k < delay:
            continue
        age = k - delay
        sgn = [-1, 1][j]
        dx = sgn * motion([676, 534, 330, 169, 68, 16, -4, 0], age)
        dy = motion([66, 47, 30, 14, 4, -2, 0], age)
        ang = sgn * motion([15, 13, 9, 5, 2.5, 0.3, -1, 0.8], age)
        ticket = label_price(j, max(-1, min(7, age - 5)))
        paste(im, ticket, ([309, 741][j] + shift + dx, 1265 + dy), ang, 1, 0.85)
    if k >= 33:
        n = k - 33
        off = motion([439, 343, 209, 91, 22, -6, 0], n)
        slip = request_slip.copy()
        if n >= 7:
            pts = [(672, 80), (695, 78), (724, 77), (753, 77), (783, 76), (806, 78)]
            last = min(6, n - 5)
            ImageDraw.Draw(slip).line(pts[:last], fill=(162, 91, 63), width=3)
        paste(
            im,
            slip,
            (524 + shift, 1447 + off),
            motion([-4, -3.2, -1.8, -0.9, 0.4, 0.8, 0.2], n),
            1,
            0.70,
        )
    if k >= 37:
        # The painted star follows an arc around the prices and seals the order slip.
        path = [
            (892, 967),
            (940, 1014),
            (971, 1084),
            (986, 1184),
            (990, 1310),
            (985, 1435),
            (954, 1524),
            (891, 1570),
            (812, 1589),
            (729, 1574),
            (659, 1541),
            (606, 1490),
            (573, 1441),
            (569, 1435),
            (570, 1446),
        ]
        n = k - 37
        xx, yy = motion(path, n)
        fac = motion(
            [
                0.33,
                0.63,
                0.84,
                1.03,
                1.1,
                1.12,
                1.12,
                1.1,
                1.07,
                1.04,
                1.01,
                1,
                0.98,
                1.01,
                1,
            ],
            n,
        )
        paste(
            im,
            stamped_star(55, 0),
            (xx + shift, yy),
            motion(
                [0, 15, 33, 57, 79, 105, 132, 158, 180, 211, 235, 257, 276, 283, 280], n
            ),
            fac,
            0.36,
        )


def sale15(k):
    im = ground.copy()
    sparkle(
        im, 79 + k, [(137, 512, 86), (894, 485, 111), (946, 554, 52), (138, 874, 80)]
    )
    if k < 8:
        dx = motion([0, -14, -72, -192, -401, -673, -945, -1250], k)
        note_scene(im, 45, dx)
    sale_parts(im, k)
    return im


mount15 = wheat((697, 988), PAPER, 520)


def artist15(im, k):
    x = motion([1190, 1110, 892, 596, 351, 173, 64, 11, -6, 0], k)
    y = motion([94, 84, 66, 50, 30, 13, 4, -2, 0], k)
    ang = motion([-14, -13, -10, -7, -3.5, -0.8, 1.5, 2.6, 1.2, 1.8], k)
    mount = mount15.copy()
    if k >= 10:
        f = book(104, "italic")
        xstart = (mount.width - f.getlength("Raynara")) / 2
        baseline_letters(
            mount,
            "Raynara",
            xstart,
            934,
            104,
            "italic",
            RED,
            k - 10,
            [0, 1, 2, 3, 4, 5, 6],
        )
    paste(im, mount, (527 + x, 918 + y), ang, 1, 1.03)
    if k >= 3:
        age = k - 3
        dx = motion([-217, -173, -111, -50, -16, 3, 0], age)
        dy = motion([-330, -259, -174, -95, -39, -9, 3, 0], age)
        phi = math.radians(ang)
        lx = -0.5 + dx
        ly = -76 + dy
        xx = 527 + x + lx * math.cos(phi) + ly * math.sin(phi)
        yy = 918 + y - lx * math.sin(phi) + ly * math.cos(phi)
        paste(
            im,
            portrait,
            (xx, yy),
            ang + motion([8, 6.7, 5, 3, 1.5, -0.5, 0], age),
            1,
            motion([1.15, 0.95, 0.8, 0.61, 0.38, 0.15, 0], age),
        )
    if k >= 12:
        age = k - 12
        off = motion([-213, -132, -61, -20, -3, 0], age)
        paste(
            im,
            tape,
            (255 + off / 4, 445 + off),
            motion([40, 34, 26, 21, 17], age),
            1,
            0.24,
        )


def outro15(k):
    im = ground.copy()
    sparkle(
        im,
        k + 147,
        [
            (131, 653, 104),
            (903, 471, 138),
            (943, 558, 57),
            (847, 1452, 90),
            (185, 1470, 60),
        ],
    )
    if k < 8:
        dx = motion([0, -18, -79, -210, -421, -727, -1010, -1310], k)
        sale_parts(im, 62, dx)
    artist15(im, k)
    return im


if __name__ == "__main__":
    compor(work / "cue.wav")
    prepare_brush()

    for base, fn, num in [
        (0, intro15, 28),
        (28, santa15, 37),
        (65, note15, 47),
        (112, sale15, 63),
        (175, outro15, 29),
    ]:
        for k in range(num):
            fn(k).convert("RGB").save(
                work / f"pose-{base + k:03}.jpg", quality=95, subsampling=0
            )
        print(f"{fn.__name__}: {num} poses", flush=True)
    # An Instagram-compatible 30 fps file, exposing each stop-motion pose for three frames.
    out = work / "reel-cartoes-de-natal-v15.mp4"
    run(
        "-y",
        "-framerate",
        "10",
        "-start_number",
        "0",
        "-i",
        work / "pose-%03d.jpg",
        "-i",
        work / "cue.wav",
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-map_metadata",
        "-1",
        "-vf",
        "scale=1080:1920:out_color_matrix=bt709:out_range=tv,setsar=1,fps=30,format=yuv420p",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        16,
        "-threads",
        5,
        "-colorspace",
        "bt709",
        "-color_range",
        "tv",
        "-color_primaries",
        "bt709",
        "-color_trc",
        "bt709",
        "-af",
        "loudnorm=I=-17:TP=-1.5:LRA=8,aresample=48000",
        "-c:a",
        "aac",
        "-b:a",
        "224k",
        "-movflags",
        "+faststart+write_colr",
        "-t",
        "20.4",
        out,
    )
    check = run("-i", out, "-f", "null", "-")
    assert re.search(r"frame=\s*612\b", check) and "Duration: 00:00:20.40" in check
    assert re.search(r"Video: h264.*1080x1920.*30 fps", check) and "Audio: aac" in check
    assert len(list(work.glob("pose-*.jpg"))) == 204
    for k in range(25):
        wanted = ground.copy()
        sparkle(
            wanted, k, [(176, 633, 104), (865, 483, 128), (934, 559, 56), (177, 1492, 73)]
        )
        envelope(wanted)
        rect = (0, LIP, W, H)
        assert (
            ImageChops.difference(
                santa15(k).crop(rect).convert("RGB"), wanted.crop(rect).convert("RGB")
            ).getbbox()
            is None
        )
    assert positions[-1] + insert.height < LIP - 80
    times = [
        0.3,
        1.3,
        3.0,
        4.4,
        5.7,
        6.7,
        7.27,
        7.65,
        8.4,
        10.8,
        12.8,
        13.95,
        14.9,
        16.45,
        18.3,
        20.1,
    ]
    panel = Image.new("RGB", (8 * 178, 2 * 343), (34, 36, 30))
    for j, t in enumerate(times):
        p = work / f"check-{j}.jpg"
        run(
            "-y",
            "-ss",
            t,
            "-i",
            out,
            "-frames:v",
            1,
            "-vf",
            "scale=176:313",
            "-update",
            1,
            p,
        )
        x = j % 8 * 178
        y = j // 8 * 343
        panel.paste(photo(p), (x, y))
        ImageDraw.Draw(panel).text(
            (x + 5, y + 316), f"{t:.2f} s", font=sans(16), fill="white"
        )
    panel.save(work / "review.jpg", quality=94)
    print(
        "204 poses, 612 frames at 30 fps, 20.40 s, AAC; all 25 pocket poses verified",
        flush=True,
    )

    os.replace(out, build / out.name)
    os.replace(work / "review.jpg", build / "quadros-v15.jpg")
    temp.cleanup()
