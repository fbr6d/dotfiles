#!/bin/bash
# 표 조립 → 자체 점검 → 국어·수학·과학 전수 검증.  결과는 run_verify.log 와 verify_*.json
cd /home/leejaeik/.hermes/profiles/miku/cache/scratch/pua_review/build || exit 1
O=$HOME/.local/share/backups/ksat-admin-skill-ops-20261125/ops24
/usr/bin/python3 assemble.py cells_all.pkl "$O" proj/tools/glyph 2>&1 | grep -a -E '^(ASusic|Amsusic|EH|GS|HancomEQN|HyhwpEQ|KO|Kab|SYM|TK) |따르는|확인 거리|읽기 없는'
/usr/bin/python3 proj/tools/pdf_glyph_text.py --selftest 2>&1 | tail -n 1
for s in ko math sci; do
  echo "== $s"
  nice -n 10 /usr/bin/python3 verify_corpus.py ../list_$s.txt verify_$s.json 6 proj/tools 2>&1 | tail -n 3
done
mkdir -p "$O/build"
cp -p *.py *.sh verify_*.json "$O/build/" 2>/dev/null
rm -rf "$O/build/proj"; cp -rp proj "$O/build/proj"
echo 끝
