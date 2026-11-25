"""wiki/ 와 주요 산출물에서 옛한글이 어떤 꼴로 저장돼 있는지 (읽기 전용)"""
import os, re, collections, unicodedata
ROOT = '/home/leejaeik/Projects/ksat-10000/'
jamo = re.compile('[\u1100-\u11ff\ua960-\ua97f\ud7b0-\ud7ff]+')
pua = re.compile('[\ue000-\uf8ff]')
compat_old = re.compile('[\u3165-\u318e]')   # 호환 자모의 옛 글자(ㆍ ㅿ ㆁ ㆆ ㅸ 등)
def scan(top, exts=('.md', '.json', '.jsonl')):
    st = collections.Counter(); ex = []
    for dp, dn, fn in os.walk(ROOT + top):
        for f in fn:
            if not f.endswith(exts): continue
            try: s = open(os.path.join(dp, f), encoding='utf-8', errors='ignore').read()
            except OSError: continue
            st['파일'] += 1
            runs = jamo.findall(s)
            if runs:
                st['첫가끝 든 파일'] += 1; st['첫가끝 글자'] += sum(len(r) for r in runs); st['첫가끝 덩이'] += len(runs)
                # 완성형 바로 뒤에 옛 끝소리가 붙은 꼴(NFC 꼴)
                st['완성형+끝소리 꼴'] += len(re.findall('[\uac00-\ud7a3][\u11a8-\u11ff\ud7cb-\ud7fb]', s))
                st['NFC로 바뀌는 덩이'] += sum(1 for r in runs if unicodedata.normalize('NFC', r) != r)
                if len(ex) < 3: ex.append((os.path.join(dp, f)[len(ROOT):][-70:], runs[:4]))
            n = len(pua.findall(s))
            if n: st['PUA 든 파일'] += 1; st['PUA 글자'] += n
            m = len(compat_old.findall(s))
            if m: st['호환 옛 자모(ㆍㅿㆁ 등) 글자'] += m
    return st, ex
for top in ('wiki', 'derived/study-cycle-02', 'derived/llm-wiki/releases', 'derived/llm-wiki/memorization/v20', 'derived/llm-wiki/memorization/v19'):
    st, ex = scan(top)
    print(top, dict(st))
    for e in ex[:2]: print('    예:', e)
