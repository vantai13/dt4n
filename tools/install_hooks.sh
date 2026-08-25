#!/bin/sh
# Cai hook vao .git/hooks/. PHAI chay lai tren moi ban clone MOI.
#
# `.git/` KHONG duoc git theo doi, nen hook khong di theo repo. Day la cung
# mot lop van de voi bit `chmod a-w` cua custody (`L84`): mot hang rao cuc bo
# theo may, khong theo du lieu. Vi vay hook duoc VERSION o `tools/hooks/` va
# chi duoc COPY vao `.git/hooks/` boi script nay.
set -e
root="$(git rev-parse --show-toplevel)"
for h in "$root"/tools/hooks/*; do
    name="$(basename "$h")"
    cp "$h" "$root/.git/hooks/$name"
    chmod +x "$root/.git/hooks/$name"
    echo "da cai: .git/hooks/$name"
done
