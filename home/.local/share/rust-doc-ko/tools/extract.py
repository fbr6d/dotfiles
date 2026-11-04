#!/usr/bin/env python3
"""Split Rust std doc comments (from the backup in ../original) into prose
paragraphs, grouped by priority tier, as JSONL chunks for translation.
Code blocks are skipped; each paragraph is keyed by a hash of its normalized
English text so the same paragraph is translated only once.
  extract.py [tier...]  -> ../work/<tier>/chunk_NN.jsonl (all tiers, or only those named)
"""
import hashlib, json, os, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, 'original')
WORK = os.path.join(BASE, 'work')
CHUNK_CHARS = 20000
LINKDEF = re.compile(r'^\s*\[[^\]]+\]:\s*\S')

TIERS = [
    ('tier1', [  # everyday types
        'alloc/src/string.rs', 'alloc/src/str.rs', 'alloc/src/vec/mod.rs', 'core/src/option.rs',
        'core/src/result.rs', 'core/src/iter/traits/iterator.rs', 'core/src/str/mod.rs',
        'std/src/collections/hash/map.rs', 'core/src/slice/mod.rs', 'alloc/src/slice.rs',
    ]),
    ('tier2', [  # common traits, formatting, smart pointers, other collections
        'core/src/ops', 'core/src/cmp.rs', 'core/src/clone.rs', 'core/src/convert', 'core/src/default.rs',
        'core/src/marker.rs', 'core/src/fmt', 'alloc/src/fmt.rs', 'std/src/macros.rs', 'alloc/src/macros.rs',
        'core/src/macros', 'alloc/src/boxed.rs', 'alloc/src/rc.rs', 'alloc/src/sync.rs', 'alloc/src/borrow.rs',
        'std/src/collections', 'alloc/src/collections', 'core/src/iter', 'core/src/char', 'core/src/hash',
    ]),
    ('tier3', [  # io, files, processes, threads, the rest of the core set
        'std/src/io', 'std/src/fs.rs', 'std/src/env.rs', 'std/src/process.rs', 'std/src/path.rs',
        'std/src/time.rs', 'std/src/thread', 'std/src/sync', 'core/src/cell.rs', 'core/src/mem',
        'core/src/num/mod.rs', 'core/src/primitive_docs.rs', 'core/src/str', 'core/src/slice', 'alloc/src/vec',
    ]),
]


def norm(s):
    s = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', s)       # [text](url)  -> text
    s = re.sub(r'\[(`[^`]*`)\]\[[^\]]*\]', r'\1', s)      # [`x`][path]  -> `x`
    s = re.sub(r'\[(`[^`]*`)\]', r'\1', s)               # [`x`]        -> `x`
    return re.sub(r'\s+', ' ', s).strip()


def key(text):
    return hashlib.sha1(text.encode()).hexdigest()[:12]


def files(spec):
    p = os.path.join(SRC, spec)
    if os.path.isfile(p):
        yield p
    else:
        for d, _, fs in sorted(os.walk(p)):
            for f in sorted(fs):
                if f.endswith('.rs'):
                    yield os.path.join(d, f)


def paragraphs(path):
    block, start = [], 0
    lines = list(open(path, encoding='utf-8', errors='replace')) + ['']
    for n, line in enumerate(lines, 1):
        m = re.match(r'\s*//[/!] ?(.*)$', line)
        if m and not line.lstrip().startswith('////'):
            if not block:
                start = n
            block.append(m.group(1))
            continue
        if block:
            fence, cur = False, []
            for b in block + ['']:
                s = b.lstrip()
                if s.startswith('```'):
                    fence, cur = not fence, []
                    continue
                if fence:
                    continue
                if not b.strip() or s.startswith('#'):
                    if cur:
                        # skip link reference definitions ([`x`]: path) - not prose
                        if not all(LINKDEF.match(c) for c in cur):
                            yield norm(' '.join(cur)), start
                        cur = []
                    if s.startswith('#') and b.strip():
                        yield norm(b.lstrip('# ')), start
                else:
                    cur.append(b)
            block = []


def main(only=None):
    seen = set()
    for tier, specs in TIERS:
        write = only is None or tier in only
        out_dir = os.path.join(WORK, tier)
        items = []
        for spec in specs:
            for f in files(spec):
                rel = os.path.relpath(f, SRC)
                for text, line in paragraphs(f):
                    if not re.search(r'[A-Za-z]{3}', text):
                        continue
                    k = key(text)
                    if k in seen:
                        continue
                    seen.add(k)
                    items.append({'id': k, 'src': f'{rel}:{line}', 'en': text})
        chunks, cur, size = [], [], 0
        for it in items:
            if cur and size + len(it['en']) > CHUNK_CHARS:
                chunks.append(cur); cur, size = [], 0
            cur.append(it); size += len(it['en'])
        if cur:
            chunks.append(cur)
        if write:
            os.makedirs(out_dir, exist_ok=True)
            for old in os.listdir(out_dir):
                os.remove(os.path.join(out_dir, old))
        for i, c in enumerate(chunks if write else [], 1):
            with open(os.path.join(out_dir, f'chunk_{i:02d}.jsonl'), 'w') as fh:
                for it in c:
                    fh.write(json.dumps(it, ensure_ascii=False) + '\n')
        print(f'{tier}: {len(items)} paragraphs, {sum(len(i["en"]) for i in items)} chars, {len(chunks)} chunks')


if __name__ == '__main__':
    import sys
    main(set(sys.argv[1:]) or None)  # extract.py tier2 -> rewrite only tier2
