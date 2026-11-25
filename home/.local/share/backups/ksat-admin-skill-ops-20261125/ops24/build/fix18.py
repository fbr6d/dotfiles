p = 'proj/tools/pdf_glyph_text.py'
s = open(p).read()

# 1) 근거 그림: 글자가 실제로 쓴 글꼴 객체로 글리프를 그린다(같은 이름의 글꼴 조각이 여럿일 때 다른 글리프가 그려지지 않게)
old = """                        info.append({'i': len(buf), 'ucs': '%04X' % ucs, 'font': cn, 'text': text, 'status': status, 'pos': pos, 'role': role, 'id': eid, 'how': how,
                                     'x': round(o[0], 1), 'y': round(o[1], 1), 'size': round(size or 0, 1), 'gid': gid})
"""
new = """                        info.append({'i': len(buf), 'ucs': '%04X' % ucs, 'font': cn, 'text': text, 'status': status, 'pos': pos, 'role': role, 'id': eid, 'how': how,
                                     'x': round(o[0], 1), 'y': round(o[1], 1), 'size': round(size or 0, 1), 'gid': gid, '_xr': list(xr)})
"""
assert old in s; s = s.replace(old, new)

old = """        xr = name2x.get(font) or n2x.get(font, ())
        g = None
"""
new = """        xr = c.get('_xr') or name2x.get(font) or n2x.get(font, ())
        g = None
"""
assert old in s; s = s.replace(old, new)

old = """                out.write(json.dumps({'page': pno + 1, 'line': i + 1, 'bbox': ln['bbox'], 'text': ln['text'], 'chars': ln['chars']}, ensure_ascii=False) + '\\n')
"""
new = """                chars = [{k: v for k, v in c.items() if not k.startswith('_')} for c in ln['chars']]
                out.write(json.dumps({'page': pno + 1, 'line': i + 1, 'bbox': ln['bbox'], 'text': ln['text'], 'chars': chars}, ensure_ascii=False) + '\\n')
"""
assert old in s; s = s.replace(old, new)

# 2) 근거 그림의 '바꾼 글자': 한글·한자는 Noto Serif CJK, 기호·로마자는 FreeSerif(없으면 Noto)로 그린다
old = """    except Exception:
        F = FT = ImageFont.load_default()
"""
new = """    except Exception:
        F = FT = ImageFont.load_default()
    FS = None
    for fp in ('/usr/share/fonts/gnu-free/FreeSerif.otf', '/usr/share/fonts/TTF/DejaVuSerif.ttf'):
        if os.path.exists(fp):
            try:
                FS = ImageFont.truetype(fp, 30)
                break
            except Exception:
                pass

    def pick(text):
        if FS is None or any(0x1100 <= ord(ch) <= 0x11FF or 0x2E80 <= ord(ch) <= 0xD7FF or 0xF900 <= ord(ch) <= 0xFAFF or 0xA960 <= ord(ch) <= 0xA97F for ch in text):
            return FT
        try:
            if FS.getmask(text).getbbox() is None:
                return FT
        except Exception:
            return FT
        return FS
"""
assert old in s; s = s.replace(old, new)
old = """        d.text((100, y0 + 14), text if len(text) <= 6 else text[:6], font=FT, fill=col.get(status, (0, 0, 0)))
"""
new = """        shown = text if len(text) <= 6 else text[:6]
        d.text((100, y0 + 14), shown, font=pick(shown), fill=col.get(status, (0, 0, 0)))
"""
assert old in s; s = s.replace(old, new)
open(p, 'w').write(s)
print('ok')
