# AMENDMENT 23-8 -- Pre-register shrinkage prediction for Lesson 23.3

Ngay: 2026-08-14

Ly do: co che hau nghiem cua Lesson 23.1 goi y mot du doan co the sai cho
Lesson 23.3; du doan nay duoc khoa truoc khi chay Lesson 23.3.

## Co che

Tai che do tin hieu yeu, `m_hat < kappa * q_hat(z)` noi rang khoang cach twin
thay duoc nho hon do bat dinh cua chinh twin tai tuoi do. Khi do argmin cua
twin giau nhieu nhieu hon tin hieu; fallback F2 STATIC co the doc nhu shrinkage
ve prior cau truc P1.

`q_hat(z)` la thanh phan quan trong: no chuan hoa `m_hat` theo do bat dinh o
tuoi tuong ung, nen co kha nang tach hai truong hop:

```text
(a) hai duong that su gan nhau       -> sai re tren thang regret
(b) twin sai ve khoang cach duong    -> sai dat tren thang regret
```

## Du doan khoa cho Lesson 23.3

```text
[CO CHE] O che do tin hieu yeu, khoang cach C3 vs B2 lon hon tren thang
regret so voi thang err.

Cu the:
  [err(C3) / err(B2)] - [regret(C3) / regret(B2)] > 0.05

Ly do: B2 dung nguong hang tren m_hat, khong chuan hoa theo q_hat(z), nen
khong tach tot truong hop (a) khoi (b). C3 co q_hat(z), nen loi ich cua C3
phai hien ro hon tren regret, noi truong hop (b) dat hon.
```

Neu du doan nay trung, no duoc tinh la prediction cua Lesson 23.3. Neu sai,
co che shrinkage/q_hat phai bi sua lai, khong duoc doi dinh nghia sau khi xem
ket qua.
