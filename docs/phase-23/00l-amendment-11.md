# AMENDMENT 23-11 -- AURC grid-density confound

Ngay: 2026-08-14

Ly do: khi kiem toan artifact Lesson 23.2, phat hien AURC toan dai bi anh
huong boi mat do nut coverage khac nhau giua hai ho nguong. Day la loi thiet
bi do, khong phai thay doi do nhin ket qua cua mot baseline moi.

## Van de

```text
luoi NHAN : 19 diem kappa, 18 coverage phan biet
luoi CONG : 14 diem epsilon, 13 coverage phan biet
```

Trong vung coverage `[0.43, 0.85]`, NHAN co 7 nut trong khi CONG chi co 3
nut. Voi duong cong loi, quy tac hinh thang tren luoi thua lam AURC tang gia.

Kiem dinh tren artifact 23.2:

```text
AURC_err(NHAN, luoi goc)             = 0.252450
AURC_err(NHAN, lay mau tren luoi CONG)= 0.253428
grid-density inflation               = +0.000978

AURC_err(NHAN) - AURC_err(CONG)       = -0.001896
diff sau khi khop mat do luoi         = -0.000918
```

Khoang 52% hieu AURC err ban dau den tu mat do luoi. Dau ket luan khong doi,
nhung bien do AURC khong duoc doc nhu hieu ung phuong phap neu chua chinh.

## Xu ly

1. Lam day luoi `delta` cua ho CONG, dac biet vung coverage trung-cao.
2. Moi so sanh AURC giua hai ho phai bao cao canh bao mat do luoi cho den khi
   luoi da khop tot.
3. Ket luan Lesson 23.2 khong dua vao AURC: no dua vao paired delta tai
   coverage khop va Pareto tren sweep gop.

Delta bo sung:

```text
{0.30, 0.35, 0.40, 0.45, 0.55, 0.60, 0.65, 0.70, 0.85, 0.90}
```

Luoi CONG sau amendment co 24 diem, gan hon mat do cua luoi NHAN trong vung
coverage trung-cao.
