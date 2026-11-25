p = 'glyphcore.py'
s = open(p).read()
old = """                sd.xref_set_key(pg.xref, 'Contents', '%d 0 R' % c)
                self._scratch = (sd, pg.number, pg.xref, c)
            sd, pno, pxref, c = self._scratch
            sd.xref_set_key(pxref, 'Resources', '<</Font<</T3 %d 0 R>>>>' % xref)
            sd.update_stream(c, b'BT /T3 100 Tf 1 0 0 1 100 150 Tm <%02X> Tj ET' % gid)
            pg = sd.reload_page(sd[pno])
"""
new = """                sd.xref_set_key(pg.xref, 'Contents', '%d 0 R' % c)
                self._scratch = (sd, pg.number, pg.xref, c)
                del pg            # 쪽 객체를 쥐고 있으면 다음에 새로 읽히지 않는다
            sd, pno, pxref, c = self._scratch
            sd.xref_set_key(pxref, 'Resources', '<</Font<</T3 %d 0 R>>>>' % xref)
            sd.update_stream(c, b'BT /T3 100 Tf 1 0 0 1 100 150 Tm <%02X> Tj ET' % gid)
            pg = sd.load_page(pno)
"""
assert old in s; s = s.replace(old, new)
open(p, 'w').write(s)
print('ok')
