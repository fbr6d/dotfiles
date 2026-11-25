# -*- coding: utf-8 -*-
"""칸 목록 → 눈으로 볼 견본 그림(sheet)과 칸 목록 JSON.

A (빈칸 읽기): 글리프 그림 + 실제 쪽 문맥 두 곳. 후보·뽑힌 글자는 그리지 않는다.
B (후보 대조): 글리프 그림 + PDF 글자층이 준 글자(후보) + 문맥.
C (옛한글 대조): 글리프 그림 + 한양 표가 가리키는 글자(Noto로 그림) + 문맥.
실행: /usr/bin/python3 mk_sheets.py <cells.pkl> <out_dir> [가족,가족…]
"""
import sys, os, io, json, pickle, re, collections
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pymupdf
from pymupdf import mupdf
import glyphcore as gc

pymupdf.TOOLS.mupdf_display_errors(False)
RAW = '/home/leejaeik/Projects/ksat-10000/raw/'
FN = '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc'
F_NO = ImageFont.truetype(FN, 22, index=1)
F_NO_S = ImageFont.truetype(FN, 17, index=1)
F_SM = ImageFont.truetype(FN, 11, index=1)
F_HD = ImageFont.truetype(FN, 16, index=1)
OLD = re.compile(r'^(Haansoft|\*옛한글|HCRBatang|T\d\d$|\*신명-중명조|TT3678AC74tCID|NewGulim)')

LAY = {
    'A': dict(cw=296, ch=252, cols=5, rows=5, gpx=56, pw=124, ph=124, ex0=-0.6, ey0=-1.5, ctx=2, cpx=24, cwem=11.6, chem=2.4),
    'B': dict(cw=370, ch=100, cols=4, rows=12, gpx=42, pw=92, ph=92, ex0=-0.6, ey0=-1.5, ctx=1, cpx=20, cwem=8.8, chem=3.0),
    'C': dict(cw=246, ch=178, cols=6, rows=7, gpx=72, pw=100, ph=100, ex0=-0.2, ey0=-1.07, ctx=1, cpx=22, cwem=10.6, chem=2.6),
}


def pick(cell, k):
    """문맥으로 쓸 표본 k개: 바로 선 글자, 크기 5~40pt, 서로 다른 PDF 먼저, 대표 모양 먼저."""
    ss = [s for s in cell['samples'] if s[7] and 5 <= s[4] <= 40]
    if not ss:
        ss = list(cell['samples'])
    ss.sort(key=lambda s: (s[8] != cell['id'], s[0]))
    out = []; seen = set()
    for s in ss:
        if s[0] in seen:
            continue
        seen.add(s[0]); out.append(s)
        if len(out) >= k:
            break
    for s in ss:
        if len(out) >= k:
            break
        if s not in out:
            out.append(s)
    return out


def work(arg):
    path, reqs = arg
    res = []
    try:
        doc = pymupdf.open(path)
        dg = gc.DocGlyphs(doc)
        pages = {}
        for (cid, slot, pno, ox, oy, size, gid, xref, gpx, cpx, cwem, chem, tick) in reqs:
            item = {'cid': cid, 'slot': slot}
            try:
                page = pages.get(pno)
                if page is None:
                    page = pages[pno] = doc[pno]
                if slot == 0:
                    f = dg.font(xref) if xref else None
                    if f is not None:
                        g = gc.render_gray(f, gid, gpx)
                        if g is not None:
                            item['glyph'] = (g[0], g[1], g[2].tobytes(), g[2].shape)
                            try:
                                item['adv'] = float(mupdf.fz_advance_glyph(f.this, gid, 0))
                            except Exception:
                                item['adv'] = None
                z = max(0.8, min(14.0, cpx / size))
                left = cwem * 0.45
                clip = pymupdf.Rect(ox - left * size, oy - chem * 0.68 * size, ox + (cwem - left) * size, oy + chem * 0.32 * size) & page.rect
                if not clip.is_empty:
                    pm = page.get_pixmap(matrix=pymupdf.Matrix(z, z), clip=clip, colorspace=pymupdf.csRGB, alpha=False)
                    item['ctx'] = (pm.width, pm.height, pm.samples)
                    item['tick'] = ((ox + tick * size - clip.x0) * z, (oy - clip.y0) * z)
            except Exception as e:
                item['err'] = '%s: %s' % (type(e).__name__, str(e)[:120])
            res.append(item)
        doc.close()
    except Exception as e:
        return path, res, '%s: %s' % (type(e).__name__, str(e)[:120])
    return path, res, None


def glyph_panel(g, adv, L, shape_em=None):
    pw, ph, gpx = L['pw'], L['ph'], L['gpx']
    im = Image.new('RGB', (pw, ph), (255, 255, 255))
    d = ImageDraw.Draw(im)
    if g is None:
        d.text((6, ph // 2 - 8), '그림 없음', font=F_SM, fill=(200, 0, 0))
        return im
    x, y, raw, shp = g
    a = np.frombuffer(raw, np.uint8).reshape(shp) if shp[0] and shp[1] else np.zeros((0, 0), np.uint8)
    pox, poy = -L['ex0'] * gpx, -L['ey0'] * gpx
    s = 1.0
    if a.size:
        gx0, gy0, gx1, gy1 = pox + x, poy + y, pox + x + a.shape[1], poy + y + a.shape[0]
        if gx0 < 2 or gy0 < 2 or gx1 > pw - 2 or gy1 > ph - 2:
            bw, bh = a.shape[1], a.shape[0]
            s = min(1.0, (pw - 16) / max(1, bw), (ph - 16) / max(1, bh))
            nw, nh = max(1, int(round(bw * s))), max(1, int(round(bh * s)))
            a = np.asarray(Image.fromarray(a).resize((nw, nh), Image.LANCZOS))
            # 글리프를 가운데 두고 원점·기준선은 그에 맞춰 옮긴다
            cx, cy = pw / 2, ph / 2
            nx0, ny0 = cx - nw / 2, cy - nh / 2
            pox = nx0 - x * s; poy = ny0 - y * s
            gx0, gy0 = nx0, ny0
        # 안내선: 기준선(가로), 글자 칸 왼쪽·오른쪽(세로 점선)
        if 0 <= poy < ph:
            d.line([(0, poy), (pw, poy)], fill=(150, 190, 255), width=1)
        for vx in ([pox] + ([pox + adv * gpx * s] if adv else [])):
            if 0 <= vx < pw:
                for yy in range(0, ph, 6):
                    d.line([(vx, yy), (vx, yy + 2)], fill=(170, 205, 255), width=1)
        ink = Image.fromarray((255 - a).astype(np.uint8)).convert('L')
        base = Image.new('L', (pw, ph), 255)
        base.paste(ink, (int(round(gx0)), int(round(gy0))))
        arr = np.asarray(im).copy()
        m = np.asarray(base).astype(np.float32) / 255.0
        arr = (arr * m[:, :, None]).astype(np.uint8)
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
    else:
        if 0 <= poy < ph:
            d.line([(0, poy), (pw, poy)], fill=(150, 190, 255), width=1)
        d.text((6, 4), '빈 글리프', font=F_SM, fill=(120, 120, 120))
    if s < 0.999:
        d.text((2, ph - 14), '축소 %.2f배' % s, font=F_SM, fill=(200, 80, 0))
    d.rectangle([0, 0, pw - 1, ph - 1], outline=(120, 120, 120))
    return im


def ctx_image(c, maxw, maxh):
    if c is None:
        im = Image.new('RGB', (maxw, maxh), (245, 245, 245))
        ImageDraw.Draw(im).text((4, 4), '문맥 없음', font=F_SM, fill=(160, 160, 160))
        return im
    (w, h, samples), (tx, ty) = c
    im = Image.frombytes('RGB', (w, h), samples).convert('L').convert('RGB')   # 문맥은 회색으로(그림 용량 줄이기)
    d = ImageDraw.Draw(im)
    # 글리프 자리 표시: 위·아래 빨간 세모
    for yy, dy in ((0, 1), (h - 1, -1)):
        d.polygon([(tx - 4, yy), (tx + 4, yy), (tx, yy + dy * 6)], fill=(230, 0, 0))
    if w > maxw or h > maxh:
        # 표시가 가운데 오도록 잘라 낸다
        x0 = int(max(0, min(w - maxw, tx - maxw * 0.45))) if w > maxw else 0
        y0 = int(max(0, min(h - maxh, ty - maxh * 0.68))) if h > maxh else 0
        im = im.crop((x0, y0, min(w, x0 + maxw), min(h, y0 + maxh)))
    return im


_cf = {}


def cand_font(path, size, idx=0, raqm=False):
    k = (path, size, idx, raqm)
    if k not in _cf:
        _cf[k] = ImageFont.truetype(path, size, index=idx, layout_engine=ImageFont.Layout.RAQM if raqm else ImageFont.Layout.BASIC)
    return _cf[k]


def cand_panel(text, L, hangul=False):
    pw, ph, gpx = (L['pw'] if hangul else 62), L['ph'], L['gpx']
    im = Image.new('RGB', (pw, ph), (255, 252, 235))
    d = ImageDraw.Draw(im)
    poy = -L['ey0'] * gpx
    if hangul:
        f = cand_font('/usr/share/fonts/noto-cjk/NotoSerifCJK-Regular.ttc', gpx, 1, True)
        d.text((-L['ex0'] * gpx, poy), text, font=f, fill=(0, 0, 0), anchor='ls')
    else:
        f = cand_font('/usr/share/fonts/gnu-free/FreeSerif.otf', gpx)
        try:
            ok = f.getmask(text).getbbox() is not None
        except Exception:
            ok = False
        if not ok or ord(text[0]) > 0x2FFF:
            f = cand_font('/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc', gpx, 1)
        d.line([(0, poy), (pw, poy)], fill=(150, 190, 255), width=1)
        d.text((10, poy), text, font=f, fill=(0, 0, 0), anchor='ls')
    d.rectangle([0, 0, pw - 1, ph - 1], outline=(200, 170, 60))
    d.text((2, 0), '후보', font=F_SM, fill=(170, 120, 0))
    return im


def main():
    D = pickle.load(open(sys.argv[1], 'rb'))
    out = sys.argv[2]
    only = set(sys.argv[3].split(',')) if len(sys.argv) > 3 else None
    os.makedirs(out, exist_ok=True)
    paths = D['paths']; shapes = D['shapes']
    cells = [c for c in D['cells'] if c.get('sheet') in ('A', 'B', 'C') and c.get('inscope', True)]
    # 묶음 이름: 수식 가족은 그대로, PUA는 C=KO(옛한글), A=SYM(기호)
    groups = collections.defaultdict(list)
    for c in cells:
        g = c['fam'] if c['fam'] != 'PUA' else ('KO' if c['sheet'] == 'C' else 'SYM')
        if only and g not in only:
            continue
        groups[(g, c['sheet'])].append(c)
    reqs = collections.defaultdict(list)
    plan = {}
    for (g, t), lst in groups.items():
        L = LAY[t]

        def main_font(c):
            return max(c['keys'].items(), key=lambda kv: kv[1])[0][0]
        if t == 'C':
            lst.sort(key=lambda c: (main_font(c), c['hy']['ucs']))
        elif t == 'B':
            lst.sort(key=lambda c: (main_font(c), c['label']))
        else:
            lst.sort(key=lambda c: (main_font(c), -c['n']))
        for c in lst:
            sh = shapes[c['id']]
            tick = (sh[0] + sh[2] / 2) / gc.S
            ss = pick(c, L['ctx'])
            plan[c['id']] = ss
            for slot, s in enumerate(ss):
                reqs[paths[s[0]]].append((c['id'], slot, s[1], s[2], s[3], s[4], s[5], s[6], L['gpx'], L['cpx'], L['cwem'], L['chem'], tick))
    print('묶음', {k: len(v) for k, v in groups.items()}, 'PDF', len(reqs), flush=True)
    got = collections.defaultdict(dict)
    errs = 0
    with Pool(8) as pool:
        for path, res, err in pool.imap_unordered(work, list(reqs.items()), chunksize=2):
            if err:
                errs += 1
            for it in res:
                got[it['cid']][it['slot']] = it
    print('그림 받음', len(got), 'PDF 오류', errs, flush=True)
    manifest = []
    for (g, t), lst in sorted(groups.items()):
        L = LAY[t]
        per = L['cols'] * L['rows']
        for si in range(0, len(lst), per):
            chunk = lst[si:si + per]
            name = '%s_%s%02d' % (g, t, si // per + 1)
            Wd, Hd = L['cols'] * L['cw'], 30 + L['rows'] * L['ch']
            sheet = Image.new('RGB', (Wd, Hd), (255, 255, 255))
            d = ImageDraw.Draw(sheet)
            hint = {'A': '칸마다: 왼쪽 위 큰 그림 = 글리프 하나(가로 파란 선 = 기준선, 세로 점선 = 글자 칸 양끝), 아래 = 실제 쪽 문맥(빨간 세모 사이가 그 글리프)',
                    'B': '칸마다: 글리프 그림 | 노란 칸 = PDF 글자층이 준 후보 글자 | 문맥(빨간 세모 사이)',
                    'C': '칸마다: 글리프 그림 | 노란 칸 = 한양 표가 가리키는 옛한글(Noto 글꼴) | 문맥(빨간 세모 사이)'}[t]
            d.text((6, 4), '%s   %s' % (name, hint), font=F_HD, fill=(0, 0, 0))
            cj = {}
            for i, c in enumerate(chunk):
                no = i + 1
                x0 = (i % L['cols']) * L['cw']; y0 = 30 + (i // L['cols']) * L['ch']
                d.rectangle([x0, y0, x0 + L['cw'] - 1, y0 + L['ch'] - 1], outline=(190, 190, 190))
                its = got.get(c['id'], {})
                it0 = its.get(0, {})
                gp = glyph_panel(it0.get('glyph'), it0.get('adv'), L)
                mf = max(c['keys'].items(), key=lambda kv: kv[1])[0][0]
                if t == 'A':
                    d.text((x0 + 5, y0 + 2), str(no), font=F_NO, fill=(0, 0, 160))
                    sheet.paste(gp, (x0 + 40, y0 + 4))
                    d.text((x0 + 170, y0 + 6), mf[:20], font=F_SM, fill=(90, 90, 90))
                    for k in range(2):
                        it = its.get(k)
                        ci = ctx_image((it['ctx'], it['tick']) if it and 'ctx' in it else None, 288, 58)
                        sheet.paste(ci, (x0 + 4, y0 + 132 + k * 60))
                elif t == 'B':
                    d.text((x0 + 3, y0 + 2), str(no), font=F_NO_S, fill=(0, 0, 160))
                    sheet.paste(gp, (x0 + 34, y0 + 4))
                    sheet.paste(cand_panel(chr(c['label']), L), (x0 + 130, y0 + 4))
                    d.text((x0 + 196, y0 + 2), mf[:22], font=F_SM, fill=(90, 90, 90))
                    it = its.get(0)
                    ci = ctx_image((it['ctx'], it['tick']) if it and 'ctx' in it else None, 172, 62)
                    sheet.paste(ci, (x0 + 196, y0 + 18))
                else:
                    sheet.paste(gp, (x0 + 34, y0 + 4))
                    sheet.paste(cand_panel(c['hy']['text'], L, hangul=True), (x0 + 140, y0 + 4))
                    d.text((x0 + 3, y0 + 2), str(no), font=F_NO_S, fill=(0, 0, 160))
                    d.text((x0 + 3, y0 + 30), mf[:4], font=F_SM, fill=(90, 90, 90))
                    it = its.get(0)
                    ci = ctx_image((it['ctx'], it['tick']) if it and 'ctx' in it else None, 240, 62)
                    sheet.paste(ci, (x0 + 3, y0 + 110))
                s0 = plan[c['id']][0] if plan[c['id']] else None
                cj[str(no)] = {'cell': c['id'], 'n': c['n'], 'npdf': c['npdf'],
                               'keys': [[k[0], '%04X' % k[1], v] for k, v in sorted(c['keys'].items(), key=lambda kv: -kv[1])][:12],
                               'pdf': os.path.relpath(paths[s0[0]], RAW) if s0 else None, 'page': (s0[1] + 1) if s0 else None}
                if t == 'B':
                    cj[str(no)]['cand'] = chr(c['label'])
                if t == 'C':
                    cj[str(no)]['cand'] = c['hy']['text']; cj[str(no)]['cand_ucs'] = '%04X' % c['hy']['ucs']; cj[str(no)]['rank'] = c['hy']['rank']
            # 보는 도구가 그림 한 장을 256KB(base64) 안으로 줄여 버리므로, 색 수를 줄여 원래 크기로 전달되게 한다
            fn = os.path.join(out, name + '.png')
            for ncol in (24, 16, 12, 8):
                sheet.quantize(colors=ncol, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(fn, optimize=True)
                if os.path.getsize(fn) <= 180_000:
                    break
            json.dump(cj, open(os.path.join(out, name + '.cells.json'), 'w'), ensure_ascii=False, indent=0)
            manifest.append({'sheet': name, 'group': g, 'type': t, 'cells': len(chunk), 'size': [Wd, Hd], 'bytes': os.path.getsize(fn)})
    json.dump(manifest, open(os.path.join(out, 'manifest.json'), 'w'), ensure_ascii=False, indent=1)
    print('견본', len(manifest), '장', collections.Counter((m['group'], m['type']) for m in manifest))


if __name__ == '__main__':
    main()
