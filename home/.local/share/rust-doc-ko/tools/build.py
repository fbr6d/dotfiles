#!/usr/bin/env python3
"""Merge finished translations into one lookup table for nvim.
  work/<tier>/chunk_NN.jsonl (id, en) + ko/<tier>/chunk_NN.json (id -> ko)
  -> dict.json  {normalized English paragraph: Korean}
Chunks without a translation file yet are skipped; untranslated entries
(Korean identical to English, e.g. link definitions) are left out.
"""
import glob, json, os, re

def match_key(en):
    # also drop emphasis, bracket and backslash marks: rust-analyzer turns _x_ into *x*,
    # rewrites [links] and escapes <, so both sides are compared without them
    # (config/rust_doc_ko.lua does the same to hover text)
    return re.sub(r'\s+', ' ', re.sub(r'[*_\[\]\\]', '', en)).strip()


BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out, chunks = {}, 0
for src in sorted(glob.glob(os.path.join(BASE, 'work', '*', 'chunk_*.jsonl'))):
    tier, name = src.split(os.sep)[-2], os.path.basename(src)[:-6]
    ko_path = os.path.join(BASE, 'ko', tier, name + '.json')
    if not os.path.exists(ko_path):
        continue
    ko = json.load(open(ko_path))
    chunks += 1
    for line in open(src):
        item = json.loads(line)
        t = ko.get(item['id'])
        if t and t.strip() and t != item['en']:
            out[match_key(item['en'])] = t
with open(os.path.join(BASE, 'dict.json'), 'w') as fh:
    json.dump(out, fh, ensure_ascii=False)
print(f'{chunks} chunks, {len(out)} paragraphs -> dict.json')
