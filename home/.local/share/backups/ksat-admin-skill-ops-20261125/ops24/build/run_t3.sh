#!/bin/bash
# Type3 글꼴까지 넣은 전수 → 새 칸 → 견본 → 본 견본 폴더에 합치기
set -e
cd /home/leejaeik/.hermes/profiles/miku/cache/scratch/pua_review/build
O=$HOME/.local/share/backups/ksat-admin-skill-ops-20261125/ops24
nice -n 10 /usr/bin/python3 shape_census2.py list_first.txt list_all.txt census_shapes_t3.pkl 8 > census_shapes_t3.log 2>&1
tail -n 1 census_shapes_t3.log
../venv/bin/python mk_cells.py census_shapes_t3.pkl cells_t3.pkl census_shapes_t3.pkl.part.pkl 2>&1 | grep -a -E '칸|범위|^    \{'
/usr/bin/python3 mk_new.py cells.pkl cells_t3.pkl cells_new.pkl cells_all.pkl
/usr/bin/python3 drop_sheets.py "$O/sheets" KO3 SYM3
rm -f "$O"/sheets_t3/*.png "$O"/sheets_t3/*.json
nice -n 10 /usr/bin/python3 mk_sheets.py cells_new.pkl "$O/sheets_t3" 2>&1 | grep -a -v Warning | tail -n 1
/usr/bin/python3 merge_sheets.py "$O/sheets_t3" "$O/sheets"
cp -p cells_all.pkl cells_new.pkl census_shapes_t3.pkl "$O/build/"
echo 끝
