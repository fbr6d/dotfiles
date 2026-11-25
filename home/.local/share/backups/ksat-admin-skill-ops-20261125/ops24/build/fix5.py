p = 'proj/tools/pdf_glyph_text.py'
s = open(p).read()

# 1) 폭 없는 공백은 뺀다
old = """        if t is None and not is_pua(ucs):
            if ucs == 0xFFFD:
                return ('⟦?⟧', '미확정', 'base', 'char', None, '글자층에 코드가 없음(U+FFFD)')
            return (chr(ucs), '그대로', 'base', 'char', None, '')
"""
new = """        if t is None and not is_pua(ucs):
            if ucs == 0xFFFD:
                return ('⟦?⟧', '미확정', 'base', 'char', None, '글자층에 코드가 없음(U+FFFD)')
            if ucs in ZERO_WIDTH:
                return ('', '그대로', 'base', 'space', None, '폭 없는 공백을 뺌')
            return (chr(ucs), '그대로', 'base', 'char', None, '')
"""
assert old in s; s = s.replace(old, new)
old = "NOSHAPE = ('noembed', 'nolink', 'ambig', 'norender')\n"
new = "ZERO_WIDTH = {0x200B, 0xFEFF, 0x2060}\nNOSHAPE = ('noembed', 'nolink', 'ambig', 'norender')\n"
assert old in s; s = s.replace(old, new)

# 2) 한양 표 후보를 미확정 글자의 설명에 붙인다
old = """        self.math = []          # (이름, 정규식, 표)
        self.pua = []           # 수식 글꼴이 아닌 글꼴의 PUA 용 표 (옛한글, 기호)
        self.version = {}
"""
new = """        self.math = []          # (이름, 정규식, 표)
        self.pua = []           # 수식 글꼴이 아닌 글꼴의 PUA 용 표 (옛한글, 기호)
        self.version = {}
        self.hanyang = {}       # 한양 PUA 표(참고용): 코드 → 첫가끝 자모
        hp = os.path.join(tdir, 'hanyang_pua.json')
        if os.path.exists(hp):
            self.hanyang = {int(k, 16): v for k, v in json.load(open(hp, encoding='utf-8'))['map'].items()}
"""
assert old in s; s = s.replace(old, new)
old = "        return (mark, '미확정', 'base', 'char', None, '표에 없는 모양')\n"
new = """        how = '표에 없는 모양'
        if t is None and ucs in self.tb.hanyang:
            how += ' (옛한글 글꼴이면 한양 표 후보: %s)' % self.tb.hanyang[ucs]
        return (mark, '미확정', 'base', 'char', None, how)
"""
assert old in s; s = s.replace(old, new)

# 3) 줄 순서: 기본은 PDF에 적힌 순서, --sort 를 주면 위치 순
old = "def convert_page(conv, doc, dg, pno):\n"
new = "def convert_page(conv, doc, dg, pno, sort=False):\n"
assert old in s; s = s.replace(old, new)
old = "    rd = page.get_text('rawdict', flags=RAW_FLAGS, sort=True)\n"
new = "    rd = page.get_text('rawdict', flags=RAW_FLAGS, sort=sort)\n"
assert old in s; s = s.replace(old, new)
old = "        lines, stat = convert_page(conv, doc, dg, pno)\n"
new = "        lines, stat = convert_page(conv, doc, dg, pno, sort=args.sort)\n"
assert old in s; s = s.replace(old, new)
old = "    ap.add_argument('--tables', default=GLYPH_DIR, help='대응표 폴더')\n"
new = "    ap.add_argument('--tables', default=GLYPH_DIR, help='대응표 폴더')\n    ap.add_argument('--sort', action='store_true', help='줄을 위치 순(위→아래, 왼쪽→오른쪽)으로 다시 놓는다. 기본은 PDF에 적힌 순서')\n"
assert old in s; s = s.replace(old, new)
open(p, 'w').write(s)
print('ok')
