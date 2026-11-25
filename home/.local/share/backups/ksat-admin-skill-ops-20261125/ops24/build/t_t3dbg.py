import pickle, json, os, sys, traceback
import pymupdf, numpy as np
import glyphcore as gc
D = pickle.load(open('cells_new.pkl', 'rb'))
O = os.path.expanduser('~/.local/share/backups/ksat-admin-skill-ops-20261125/ops24')
cj = json.load(open(os.path.join(O, 'sheets', 'KO3_C01.cells.json')))
cells = {c['id']: c for c in D['cells']}
for no in ('1', '4', '8'):
    c = cells[cj[no]['cell']]
    s = [x for x in c['samples']][0]
    print('칸', no, '표본', s[:8], 'hash 같음', s[8] == c['id'], '표본 수', len(c['samples']))
    doc = pymupdf.open(D['paths'][s[0]]); page = doc[s[1]]
    dg = gc.DocGlyphs(doc)
    n2x = dg.page_map(page)
    for sp in page.get_texttrace():
        for (ucs, gid, org, bbox) in sp['chars']:
            if gid == s[5] and abs(org[0] - s[2]) < 0.2 and abs(org[1] - s[3]) < 0.2:
                xr = n2x.get(sp['font'], ())
                print('   글자층:', repr(sp['font']), hex(ucs), 'gid', gid, 'xrefs', xr, [(x, dg._type.get(x)) for x in xr], 'size', sp['size'])
                for x in xr:
                    try:
                        sd = pymupdf.open(doc.name)
                        pg = sd.new_page(width=400, height=400)
                        cx = sd.get_new_xref(); sd.update_object(cx, '<<>>'); sd.update_stream(cx, b' ')
                        sd.xref_set_key(pg.xref, 'Contents', '%d 0 R' % cx)
                        sd.xref_set_key(pg.xref, 'Resources', '<</Font<</T3 %d 0 R>>>>' % x)
                        sd.update_stream(cx, b'BT /T3 100 Tf 1 0 0 1 100 150 Tm <%02X> Tj ET' % gid)
                        pg = sd.reload_page(sd[pg.number])
                        pm = pg.get_pixmap(matrix=pymupdf.Matrix(0.72, 0.72), colorspace=pymupdf.csGRAY, alpha=False)
                        a = 255 - np.frombuffer(pm.samples, np.uint8).reshape(pm.height, pm.stride)[:, :pm.width]
                        print('      xref', x, '직접 그림: 잉크', int((a >= 24).sum()), 'gray()', None if dg.gray(x, gid, 72) is None else dg.gray(x, gid, 72)[2].shape, 'hash', dg.glyph_hash(x, gid))
                        print('      글꼴 객체:', doc.xref_object(x, compressed=True)[:230])
                    except Exception:
                        traceback.print_exc()
