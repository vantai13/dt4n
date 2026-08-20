# 06 -- TAI KHUNG: fallback la THAM SO NGOAI SINH

Ngay: 2026-08-20
Khoa boi: `00z-amendment-25.md` muc 6, `00za-amendment-26.md`, `00zc-amendment-28.md`
Tai lieu nay phai duoc doc TRUOC `11-abstain-cost.md`: no tuyen bo khung, tai
lieu kia bao cao so trong khung do.

---

## 1. Tuyen bo

```text
Fallback KHONG phai mot cau hoi nghien cuu cua do an nay. No la mot RANG BUOC
do he thong ap dat: trong mot mang SDN that, "controller du phong khi khong tin
twin" do doi van hanh quyet dinh, thuong vi ly do an toan va kiem dinh, khong
vi ly do toi uu.

Tu Lesson 23.6, fallback duoc mo hinh hoa bang MOT THAM SO NGOAI SINH `c`:
rui ro trung binh cua controller du phong tren tap hang BI TU CHOI.
```

## 2. Vi sao doi -- loi pham tru cua v1

v1 cho fallback mot pre-registration rieng, nhieu amendment, va cac GATE
`PASS`/`FAIL`. Dat gate `PASS`/`FAIL` len mot LUA CHON KE TOAN la mot **loi pham
tru**. He qua da xay ra that: gate `FAIL` bi doc thanh "phuong phap that bai",
trong khi no chi noi "P1 la mot baseline manh o che do nay".

Ba dong literature deu coi fallback la DAU VAO NGOAI SINH:

```text
Chow 1970            abstain co chi phi hang so `c` cho truoc; bao cao DUONG
                     risk-coverage, khong bao cao mot diem
learning to defer    reject chuyen cho chuyen gia; chi phi chuyen gia ngoai sinh
Simplex (Sha 2001)   baseline controller duoc verify RIENG va TRUOC; no la
                     RANG BUOC AN TOAN, khong phai doi thu de so
```

```text
NT-v2-1  Mot dai luong phu thuoc mot LUA CHON KE TOAN khong duoc mang gate
         PASS/FAIL. No duoc bao cao nhu DIAGNOSTIC.
```

## 3. Dong nhat thuc trung tam

```text
R_neo(gamma)       = gamma*R|accept + (1-gamma)*R|reject(twin)        (dinh ly)
R_system(gamma, c) = gamma*R|accept + (1-gamma)*c
Delta              = R_system - R_neo = (1-gamma)*(c - c*)
c*(gamma)         := R|reject(twin, gamma)

CO LOI  <=>  c < c*(gamma)
```

Ba tinh chat:

```text
(1) c* KHONG phu thuoc fallback nao duoc chon.
    Bang chung KIEM DUOC BANG MAY, khong phai mot cau trong docstring: chu ky
    `breakeven_c(r_reject_twin)` khong nhan tham so nao lien quan fallback.
    Thuc thi: test_phase23_abstain_cost.py::test_A21.
(2) c* DO DUOC hoan toan tu certificate + twin.
(3) => nguoi van hanh co mot CONG CU: do `err|reject` cua twin duoi certificate;
    neu baseline controller cua ho tot hon con so do, hay bat certification.
```

## 4. TRUNG THUC ve muc dong gop (K-D7)

```text
(*) la DINH LY xac suat toan phan. Do do R_system(gamma, c*) = R_neo la mot
DONG NHAT THUC, dung theo dinh nghia. `G23-32` la KIEM TRA DUNG CODE, khong
phai mot ket qua khoa hoc.
```

Va -- quan trong hon:

```text
Vung co loi KHONG duoc kham pha o Lesson 23.6. Lesson 23.3 DA DO no roi
(`beneficial_band_err`). Doi chung C23v2-1 xac nhan hai ben gap nhau trong
1.5e-4 tren ca ba cell.

Cai 23.6 lam la:
   (a) DAT TEN cho no bang mot dai luong khong nhac den P1
   (b) do no KEM DAI TIN CAY DONG THOI lan dau
   (c) tong quat hoa sang fallback BAT KY
Viet khac di la noi qua.
```

## 5. Ha cap gate -- KHONG rut so lieu nao

| Gate | v1 | v2 | Ly do |
|---|---|---|---|
| G23-8 | PASS | DIAGNOSTIC | do mot tinh chat cua che do, khong phai mot gia thuyet |
| G23-14 | PASS | DIAGNOSTIC | do mot lua chon ke toan (fallback nao tot nhat) |
| G23-15 | FAIL | DIAGNOSTIC | so sanh phu thuoc fallback |
| G23-17 | FAIL | DIAGNOSTIC | ket luan van hanh phu thuoc che do |
| G23-23 | PASS | DIAGNOSTIC | dinh luat lift>swing la dang RIENG cua Delta=(1-g)(c-c*) |

```text
KHONG mot con so nao cua v1 bi rut lai. Chi doi VAI TRO.
Neu v2 phai xoa ket qua v1 thi v2 sai chu khong phai v1.
```

Trang thai hien tai cua nam gate nay nam o `GATES.md`, cot `status`, gia tri
`DIAGNOSTIC`, kem tro toi Amendment 23-25 muc 2.

## 6. Gate nao con la GATE THAT sau tai khung

```text
CON LA GATE : bao phu conformal (G23-25), doi chung am/duong (G23-26, G23-27b),
              tai lap va toan ven artifact (G23-29, G23-33), dong nhat thuc
              dai so (G23-32), chat luong bo chon (K-6), doi chung cheo
              (C23v2-1), dinh vi fallback (G23-35), bang nguong (G23-36)
KHONG CON   : moi phat bieu dang "fallback X thang fallback Y"
```

## 7. Quan he voi dinh luat lift > swing (K23-5)

```text
K23-5 (Lesson 23.4) :  Delta = reject_share * (swing - lift)
Lesson 23.6         :  Delta = (1 - gamma)  * (c     - c*)

reject_share == 1 - gamma        swing - lift == c_F2 - c*

=> K23-5 la DANG RIENG cua dong nhat thuc 23.6 khi fallback = F2 STATIC (P1).
   Dang 23.6 tong quat hon vi no khong nhac den P1.
   v2 KHONG rut lai K23-5; v2 CHUA no.
```

## 8. Hai he qua khong luong truoc cua viec tai khung

Tai khung khong chi doi cach VIET; no lam hai dieu tro nen NHIN THAY DUOC ma
truoc do bi che khuat.

```text
(1) F1 va F3 la CUNG MOT DIEM tren truc c (F-23.6-6).
    Khi con hoi "fallback nao tot nhat", ba fallback la ba ung vien va nguoi ta
    khong hoi chung co khac nhau khong. Khi hoi "moi fallback nam o dau tren
    truc c", cau hoi "hai fallback nay co cung mot cho khong" tro thanh hien
    nhien -- va cau tra loi la CO.
    Dieu nay giai thich vi sao du doan F4 cua Lesson 23.1 la BAT KHA THI chu
    khong phai SAI (Amendment 23-29 muc 6).

(2) Diem van hanh cua Lesson 23.1 (kappa = 0.5) nam NGOAI beneficial band
    [0.6076, 0.99995]. Hai du doan F3 va F6 MISS vi ly do DO, khong vi co che
    sai. Chi khi ca duong `c*(gamma)` duoc ve ra thi dieu nay moi hien.
```

```text
Bai hoc phuong phap: tai khung mot cau hoi khong tao ra du lieu moi, nhung no
doi TAP CAU HOI ma du lieu co the tra loi. Hai su that tren da nam trong du
lieu tu Lesson 23.1; khung cu khong co cho de hoi chung.
```
