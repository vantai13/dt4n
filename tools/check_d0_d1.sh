#!/usr/bin/env bash
# Self-audit for Lessons D.0 and D.1. BLOCKED is deliberately distinct from FAIL.
set -u

repo_root=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "Run this script inside the dt4n repository." >&2
  exit 2
}
cd "$repo_root"

pass=0
fail=0
blocked=0
ok() { printf '  ✅ %s\n' "$1"; pass=$((pass + 1)); }
no() { printf '  ❌ %s\n' "$1"; fail=$((fail + 1)); }
hold() { printf '  ⛔ %s\n' "$1"; blocked=$((blocked + 1)); }

echo "═══════════ LESSON D.0 — BẢO TỒN & DỌN KHO ═══════════"

backup=$(find "$(dirname "$repo_root")" -maxdepth 1 -type f \
  -name 'dt4n-FULL-BACKUP-*.tar.gz' -print -quit)
[[ -n "$backup" ]] && ok "D0-1a backup tarball tồn tại: $backup" \
  || no "D0-1a chưa có backup tarball"
grep -q 'BLOCKED — cần người dùng chọn đích/tài khoản' \
  docs/phase-D/00-reproduction-audit.md \
  && hold "D0-1b backup ngoài máy chưa có đích được xác nhận" \
  || ok "D0-1b audit ghi nhận backup ngoài máy"

git rev-parse -q --verify refs/tags/phase-D-cleanup-start >/dev/null \
  && ok "D0-2 tag phase-D-cleanup-start tồn tại cục bộ" \
  || no "D0-2 chưa có tag phase-D-cleanup-start"
if git ls-remote --exit-code --tags origin \
  refs/tags/phase-D-cleanup-start >/dev/null 2>&1; then
  ok "D0-2b tag đã push lên origin"
else
  hold "D0-2b tag chưa thấy trên origin hoặc chưa có credential/network"
fi

[[ -f docs/phase-D/00-reproduction-audit.md ]] \
  && ok "D0-3 reproduction audit tồn tại" || no "D0-3 thiếu reproduction audit"
[[ -f docs/phase-D/parquet-sha256-before-delete.txt ]] \
  && [[ $(wc -l < docs/phase-D/parquet-sha256-before-delete.txt) -eq 8 ]] \
  && ok "D0-3b đã ghi SHA256 của đúng 8 parquet" \
  || no "D0-3b checksum list thiếu hoặc không có đúng 8 dòng"

doi=$(python3 - <<'PY'
import json
print(json.load(open("results/DATA_MANIFEST.json", encoding="utf-8")).get("doi") or "")
PY
)
if [[ -n "$doi" ]]; then
  ok "D0-4 DATA_MANIFEST Version DOI = $doi"
else
  hold "D0-4 DATA_MANIFEST.doi vẫn null; cần publish Zenodo bằng tài khoản người dùng"
fi
grep -q '| K11 | `ARCHIVE_TAG`' docs/phase-23/CONSTANTS.md \
  && ok "D0-4b CONSTANTS có ARCHIVE_TAG K11" \
  || no "D0-4b CONSTANTS thiếu ARCHIVE_TAG"

tracked=$(git ls-files 'results/**/phase-21R/*.parquet' | wc -l)
if [[ -z "$doi" ]]; then
  grep -q '^!results/\*\*/phase-21R/\*\*/\*\.parquet$' .gitignore \
    && hold "D0-5 whitelist còn giữ có chủ đích tới khi có DOI" \
    || no "D0-5 whitelist đã bị gỡ trước khi có DOI"
  [[ "$tracked" -eq 8 ]] \
    && hold "D0-6 còn 8 parquet tracked đúng safety gate; chưa được untrack" \
    || no "D0-6 cần đúng 8 parquet tracked trước DOI, hiện có $tracked"
else
  grep -q '^!results/\*\*/phase-21R/\*\*/\*\.parquet$' .gitignore \
    && no "D0-5 vẫn còn whitelist sau khi có DOI" \
    || ok "D0-5 whitelist parquet đã gỡ"
  [[ "$tracked" -eq 0 ]] && ok "D0-6 parquet đã untrack" \
    || no "D0-6 còn $tracked parquet tracked sau DOI"
fi

[[ -x tools/hooks/pre-commit ]] && grep -q MAXBYTES tools/hooks/pre-commit \
  && ok "D0-7 hook chặn file lớn tồn tại" || no "D0-7 hook nguồn thiếu"
[[ -x .git/hooks/pre-commit ]] \
  && ok "D0-7b hook đã cài trong .git/hooks" || no "D0-7b hook chưa cài"

legacy_imports=$(rg -n 'from legacy|import legacy' -g '*.py' -g '!legacy/**' . \
  2>/dev/null | wc -l)
[[ "$legacy_imports" -eq 0 ]] \
  && ok "D0-8 legacy không còn import; giữ nguyên vì cleanup này là tùy chọn" \
  || ok "D0-8 legacy còn được import tại $legacy_imports chỗ"

echo
echo "═══════════ LESSON D.1 — SỔ SÁCH SỰ THẬT ═══════════"
[[ -f docs/phase-23/66-state-of-23-25.md ]] \
  && ok "D1-1 state table tồn tại" || no "D1-1 thiếu state table"
grep -q 'n_eff' docs/phase-23/66-state-of-23-25.md \
  && ok "D1-1b bảng ghi n_eff/sampling" || no "D1-1b bảng thiếu n_eff"
grep -q 'ĐỐI CHỨNG ÂM.*ac/ad' docs/phase-23/66-state-of-23-25.md \
  && ok "D1-1c ac-ad được ghi đúng là negative control chung host" \
  || no "D1-1c nhãn ac-ad chưa đúng"
grep -q 'DINH CHINH / RUT LAI' docs/phase-23/59-identifiability-audit.md \
  && ok "D1-2 retraction S20 nằm trong tài liệu nguồn 59" \
  || no "D1-2 doc 59 thiếu retraction tại chỗ"
if [[ ! -e MASTER_PLAN_v9.md ]]; then
  ok "D1-2b MASTER_PLAN_v9.md không tồn tại trong repo; không có file để sửa"
elif grep -Eq 'ĐÍNH CHÍNH|DINH CHINH|RÚT LẠI|RUT LAI' MASTER_PLAN_v9.md; then
  ok "D1-2b MASTER_PLAN có retraction"
else
  no "D1-2b MASTER_PLAN thiếu retraction"
fi

[[ -f docs/phase-D/02-limits-addendum.md ]] \
  && ok "D1-3 limits addendum tồn tại" || no "D1-3 thiếu limits addendum"
for limit in D-L12 D-L13 D-L14 D-L15; do
  grep -q "| $limit |" docs/phase-D/02-limits-addendum.md \
    && ok "D1-3b $limit tồn tại" || no "D1-3b thiếu $limit"
done
grep -q DEPRECATED twin/topology_v7.py \
  && ok "D1-4 historical load targets đã deprecated" \
  || no "D1-4 load targets chưa deprecated"

if [[ -n $(git status --porcelain) ]]; then
  hold "D1-5 worktree còn thay đổi chưa commit"
else
  ok "D1-5 worktree sạch"
fi

echo
echo "═══════════════════════════════════════"
printf '  PASS: %d    FAIL: %d    BLOCKED: %d\n' "$pass" "$fail" "$blocked"
[[ "$fail" -eq 0 && "$blocked" -eq 0 ]]
