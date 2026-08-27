# AMENDMENT 23-73 -- SUA HAI SAI SOT TIEN DANG KY CUA `A072`

Ngay ky : 2026-08-27

Loai    : SUA SAI SOT TIEN DANG KY. KHONG dien giai lai ket qua.
          KHONG doi bat ky con so nao da do.

## 1. Sai sot 1 -- mau so bin

`A072` muc 6 ky `>= 3/5 bin` (`G23-291`) va `>= 4/5 bin` (`G23-294`).
Truc LIVE co 4 bin: `z_edges = [0.1, 0.241, 0.366, 0.491, 0.641]`.
`4/5` la mot dai KHONG THE DAT.

Xu ly: ca hai dai duoc ghi la HONG-KHI-KY. KHONG chuyen doi sang `3/4` hay
`4/4` -- doi mau so sau khi nhin du lieu la HARKing. Ket qua cua `G23-291`
va `G23-294` duoc bao cao o dang MO TA, khong duoc cham HIT/MISS.

## 2. Sai sot 2 -- `M-230` bat kha thi

`A072` muc 6 ky: "ton tai >= 1 o ma C3 tra `q_hat = +inf`".
Voi `POST_VARIANT = "selective"`: 4 o, moi o 500 block. Nguong tu choi la
29. Dai nay KHONG CO DUONG NAO de fire.

Con so 500 block/o suy duoc TRUOC khi ky, tu `M-181` (Lesson 23.7, dai
`[440, 500]` tren Mondrian 2 truc; bo mot truc thi chi tang).

Xu ly: `M-230` ghi la BAT KHA THI, khong phai MISS. `CL-13` chua duoc
kiem tren cell nao. Chuyen sang `L125`.

## 3. Quy tac moi -- ap dung tu Lesson 23.24

```text
R5  Moi dai dang "ton tai >= k o thoa X" PHAI kem mot dong DIEU KIEN KHA THI:
    gia tri tham so nao (so o, so block/o, bien truc) khien X co the xay ra.
    Va mot test cau truc kiem dieu kien do, chay TRUOC nhanh do luong.
```

`L99`, `L101`, `L119`, va hai sai sot o day la NAM lan cung mot hinh dang:
mot dai duoc ky ma khong ai kiem xem no CO THE fire hay khong. `R5` bien
viec kiem do thanh mot buoc co hoc.

## 4. Khong doi ket qua

Moi con so trong `results/LIVE/phase-23/baselines_lit.json` giu nguyen.
Amendment nay chi doi CACH CHAM DIEM cua hai dai, va chi theo huong HA
xuong MO TA -- khong bao gio nang mot MISS thanh HIT.
