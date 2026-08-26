#!/usr/bin/env bash
# Doi TRO sau tag con ket lai o lich su TRUOC lan rewrite 2026-08-23.
#
# VAN DE (`L123`): lan rewrite lich su da GO cac parquet nang khoi lich su va
# di chuyen nhanh, nhung SAU tag `amendment-49a..49f` van tro vao commit CU.
# Nhung commit do khong nam trong `main`, nen `git push --tags` phai day len
# CA lich su rieng cua chung -- do duoc **1962.85 MB** parquet ma chinh lan
# rewrite da co y go bo. Day la ly do push bi treo o "Compressing objects".
#
# `.gitignore` KHONG sua duoc viec nay: cac parquet do DA bi ignore o HEAD
# (dong 165). Chung nam trong OBJECT cua commit cu, khong phai trong cay lam
# viec. `.gitignore` chi ngan file MOI duoc them; no khong dong den lich su.
#
# AN TOAN:
#   - remote dang co 0 tag, nen khong ai khac dang giu 6 tag nay -> doi tro
#     khong pha vo ban sao cua ai.
#   - commit cu VAN SONG trong nhanh `backup-pre-rewrite-20260823`.
#   - da doi chieu: giua ban cu va ban moi, KHONG file text nao khac nhau;
#     chi 30 file parquet bi go (`git diff --name-only` loc phi-parquet = rong).
#
set -euo pipefail
TODAY="$(date -u +%Y-%m-%d)"
BACKUP_BRANCH="backup-pre-rewrite-20260823"

repoint () {   # $1 = ten tag
  local tag="$1" old new subj body
  old="$(git rev-parse "$tag^{commit}")"
  if git merge-base --is-ancestor "$old" main 2>/dev/null; then
    echo "SKIP  $tag (da tro vao lich su main)"; return
  fi
  subj="$(git log -1 --format='%s' "$old")"
  # `git log | grep -m1` sinh SIGPIPE va bi `set -o pipefail` bat -> ghi ra
  # bien truoc roi moi loc. Cham hon vai chuc mili giay, doi lai tin cay.
  local all_main
  all_main="$(git log main --format='%H %s')"
  new="$(printf '%s\n' "$all_main" | grep -F -m1 -- "$subj" | cut -d' ' -f1 || true)"
  if [ -z "$new" ]; then
    echo "FAIL  $tag: khong tim thay ban sau rewrite cho \"$subj\""; return 1
  fi
  # Bat buoc: hai commit chi duoc khac nhau o file du lieu nang.
  local changed
  changed="$(git diff --name-only "$old" "$new")"
  if printf '%s\n' "$changed" | grep -vE '\.(parquet|npz|bin)$|\.csv\.gz$' | grep -q .; then
    echo "FAIL  $tag: ban cu va ban moi khac o file KHONG phai du lieu nang"; return 1
  fi
  body="$(git for-each-ref "refs/tags/$tag" --format='%(contents)')"
  git tag -d "$tag" >/dev/null
  git tag -a "$tag" "$new" -m "$(cat <<EOF
${body}

REPOINTED $TODAY: tag nay truoc do tro vao ${old:0:8}, mot commit TRUOC lan
rewrite lich su 2026-08-23. Commit do khong nam trong \`main\`, nen
\`git push --tags\` se day len 1962.85 MB parquet ma chinh lan rewrite da go.

Ban cu van song o nhanh \`$BACKUP_BRANCH\`.
Giua ${old:0:8} va ${new:0:8} KHONG file text nao khac; chi 30 parquet bi go.
Xem docs/phase-23/LIMITS.md muc L123.
EOF
)"
  echo "MOVE  $tag  ${old:0:8} -> ${new:0:8}"
}

if ! git rev-parse -q --verify "$BACKUP_BRANCH" >/dev/null; then
  echo "DUNG: khong thay nhanh $BACKUP_BRANCH -- commit cu se mat neu doi tro."
  exit 1
fi

for t in amendment-49a amendment-49b amendment-49c amendment-49d amendment-49e amendment-49f; do
  repoint "$t"
done

echo
echo "=== KIEM: con tag nao ngoai lich su main khong? ==="
n=0
for t in $(git tag); do
  if ! git merge-base --is-ancestor "$(git rev-parse "$t^{commit}")" main 2>/dev/null; then
    echo "  CON NGOAI: $t"; n=$((n+1))
  fi
done
echo "tong: $n"
