# AMENDMENT 23-49a -- Hai sua dac ta TRUOC BUOC 5b

Ngay ky : 2026-08-22
Tag     : amendment-49a
Loai    : CORRECTION cua chinh amendment 23-49, ky TRUOC khi chay 5b

```text
DA XEM  : ket qua BUOC 5a (M-121..M-124, deu HIT) va phan bo z cua hai truc
CHUA XEM: bat ky q_hat nao tren truc moi
```

## 1. `M-125` tach lam hai -- dac ta cu SAI

Dai `+5% .. +13%` cua `M-125` suy tu ty so MEAN z (`302.5 -> 366.0`), tuc chi
dung cho `q_hat` **BIEN**. Nhung bin CU va bin MOI **khong cung khoang z**:
bin cu rong khong deu (45/100/100/250 ms, ty trong 9/20/20/51%), bin moi deu
nhau (125-150 ms, 25% moi bin).

Do tren chinh hai parquet cua BUOC 5a (z trung binh THUC trong tung bin,
khong phai trung diem canh):

```text
bin   z_tb CU    ty trong CU   z_tb MOI   ty trong MOI   ty so   q_hat du doan
B0      75.00        0.0900     178.25        0.2494     2.377      +45.2%
B1     147.50        0.2000     303.12        0.2499     2.055      +36.4%
B2     247.50        0.2000     428.12        0.2499     1.730      +26.6%
B3     424.99        0.5100     553.40        0.2509     1.302      +12.1%
                                          trung binh theo bin        +30.1%
```

```text
q_hat BIEN du doan  = +8.56%   -> nam TRONG dai +5..+13%
trung binh THEO BIN = +30.1%   -> MISS GIA voi dai cu
```

`q_hat(B0)` cu do tren `z_tb = 75 ms`; `q_hat(B0)` moi do tren `178 ms`. So
hai cai do la so HAI DAI LUONG KHAC NHAU, khong phai so tac dong cua viec
sua truc.

### Dac ta moi

```text
M-125a  q_hat BIEN (gop moi hang, KHONG bin), moi/cu      +5% .. +13%      __
        tien doan +8.56%
        => phep kiem "sua truc da dich mean z dung chua"

M-125b  moi bin: q_hat_moi(b)/q_hat_cu(b) doi chieu
        (z_tb_moi(b)/z_tb_cu(b))^0.431                    +/-25% MOI bin   __
        tien doan  B0 +45.2%  B1 +36.4%  B2 +26.6%  B3 +12.1%
        => phep kiem "dinh luat do gian con dung tren truc moi khong"
```

`M-125b` kiem dinh luat `z^0.431` o **BON diem voi bon ty so khac nhau
(1.30 den 2.38)**, manh hon han mot diem. Neu ca bon khop trong `+/-25%`, do
la mot XAC NHAN DOC LAP cho dinh luat do gian cua Phase 22 -- mot ket qua,
khong chi mot cong. Va no la dau vao truc tiep cho Lesson 23.28 (transfer
giua bin tuoi): bon ty so khop hay khong quyet dinh `z^0.431` la MO TA hay
DUNG DUOC.

`M-126` (`q_hat(B3)/q_hat(B0)` noi bo run moi) KHONG doi.

## 2. `d_base` tro thanh HAM cua ho so

Dac ta cu de `d_base = 107.775 ms` **co dinh** (bu tru cho rieng `U3`), dung
cho moi ho so. Do duoc tren truc moi:

```text
ho so   mean(off)   mean z (ms)   lech U3    -> q_hat
U0          0.000      357.889     -8.125     -0.96%
U1         22.500      380.389    +14.375     +1.67%
U2         12.500      370.389     +4.375     +0.51%
U3          8.125      366.014      0.000      0.00%
```

=> **tai lap dung confound** "hinh dang lan muc tuoi" ma `amendment 23-49
muc 3` duoc viet ra de sua. Da dong cua truoc cho `U1/U2` bang `U1c/U2c`,
nhung cua sau van mo qua `d_base`.

### Sua

```text
d_base(ho so) = D_SYNC_S - mean(off cua CHINH ho so do)
=> moi ho so cho cung mean z = D_SYNC_S + T/2, trong +/-0.01 ms
```

Nguyen tac chung, va no la buoc con thieu cua chinh nguyen tac da ap o
`u3_profile_ms`:

> **Hang so bu tru phai la HAM cua thu no bu tru.**
> Da lam dung cho `alpha -> U3`, nhung dung mot buoc som o `U3 -> d_base`.

Sau khi sua, `U1c`/`U2c` **khong con can** (bu tru da lam viec trung tam hoa,
va lam dung cho ca ho so them sau nay). GIU chung lai de khong lam churn
khoa `test_GC1_profiles_locked`, nhung ghi ro la DU THUA.

### Khoa moi

```text
M-132 *  moi ho so trong AOI_PROFILES (tru PC4) cho CUNG mean z
         trong +/-0.01 ms                                                 __
```

## 3. Bo sung `L38`

So block moi bin BANG NHAU tuyet doi (500/500/500/500) => khong phai "mot so
block cham nhieu bin" ma la **MOI block cham MOI bin**. He qua cho block
bootstrap: khi lay mau lai block, `q_hat` cua bon bin **cung dich voi nhau**.
CI tung bin van dung, nhung **phat bieu DONG THOI tren bon bin co tuong quan
chua duoc tinh**. Neu paper co cau "coverage dat tren MOI bin" thi can
Bonferroni hoac mot bootstrap giu nguyen cau truc block.

## 4. KHONG duoc lam

```text
- KHONG chay 5b truoc khi sua xong muc 1 va muc 2.
- KHONG dieu chinh dai cua M-125b sau khi thay bon ty so.
```

Chu ky: ____________
