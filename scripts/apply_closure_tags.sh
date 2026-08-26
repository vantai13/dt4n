#!/usr/bin/env bash
# Gan tag ANNOTATED cho cac trang thai da duoc claim trong doc/artifact.
#
# QUY TAC BAT BUOC:
#   1. LUON dung -a (annotated). Lightweight tag khong mang ngay tao,
#      nen khong the phan biet tag goc voi tag hoi to.
#   2. Message PHAI ghi RETROACTIVE + ngay gan + bang chung THAT o dau.
#   3. KHONG BAO GIO dung `git tag -f` de doi mot tag da push.
#   4. KHONG DOAN moc. Mot moc tien dang ky doan sai con te hon khong co
#      moc: no bien mot cho trong THANH THUC thanh mot khang dinh SAI.
#
set -euo pipefail
TODAY="$(date -u +%Y-%m-%d)"

tag_retro () {   # $1=ten  $2=commit  $3=loai  $4=bang chung that
  if git rev-parse -q --verify "refs/tags/$1" >/dev/null; then
    echo "SKIP  $1 (da ton tai)"; return
  fi
  if ! git rev-parse -q --verify "$2^{commit}" >/dev/null; then
    echo "FAIL  $1 -> commit $2 KHONG TON TAI"; return 1
  fi
  git tag -a "$1" "$2" -m "$(cat <<EOF
$3

RETROACTIVE: tag nay duoc gan ngay $TODAY, KHONG phai tai thoi diem commit
$2. Xem docs/phase-23/LIMITS.md muc L114.

Bang chung thoi diem THAT: $4
EOF
)"
  echo "TAG   $1 -> $2"
}

# ---- Phase 23: moc DA XAC MINH ------------------------------------------
tag_retro lesson-23-22-complete 18f82cd \
  "Lesson 23.22 Task A0/A/B/B-2/B-3 dong. G23-230..269: 32 PASS, 7 FAIL, 1 DIAG." \
  "commit 18f82cd (2026-08-26) + docs/phase-23/47-close-23-22.md"

tag_retro lesson-23-22-b3-prereg 5218cc7 \
  "Tien dang ky Task B-3 (amendment 23-68), G23-261..269 NOT_RUN." \
  "ngay commit cua 5218cc7 -- DAY moi la bang chung tien dang ky, khong phai tag"

tag_retro lesson-23-22d-a-prereg b1a6c8c \
  "Tien dang ky A070 nhanh W va nhanh E." \
  "ngay commit cua b1a6c8c -- DAY moi la bang chung tien dang ky, khong phai tag"

# `43-taxonomy-audit.md:7` GHI SAN hash nay, nen tag phai tro dung vao do de
# lenh trong doc chay duoc. Nhung `7c23151` la commit THEM `cert/taxonomy_audit.py`
# (600 dong ma do luong) -- tuc moc do luong, KHONG phai moc tien dang ky.
# Tag mang canh bao trong chinh message; `test_prereg_tag_carries_its_warning`
# ghim canh bao do.
tag_retro lesson-23-22-prereg 7c23151 \
  "Moc Task A0 (taxonomy_audit) nhu 43-taxonomy-audit.md muc dau ghi.

NOT PREREG EVIDENCE: 7c23151 la commit THEM cert/taxonomy_audit.py, tuc ma
DO LUONG da ton tai tai moc nay. Ten tag noi 'prereg' nhung moc thi khong.
KHONG duoc trich dan tag nay lam bang chung tien dang ky." \
  "amendment A064 = commit 53b74f7 (to tien cua 7c23151) -- trich dan 53b74f7"

# ---- Phase 20 / 20R / 21 / 21R / 22 / 23 / T ----------------------------
# 12 tag con lai KHONG duoc gan o day. Khong doc nao ghi hash, nen moi moc
# deu la mot phong doan. Xem `L114` muc (c): chung nam trong
# `UNRESOLVED_DOC_CLAIMS` cua test/test_closure_tags_exist.py kem ly do,
# va nguoi ky phai tu xac dinh moc truoc khi gan.

echo
echo "=== TAG HIEN CO ==="
git tag -n1
