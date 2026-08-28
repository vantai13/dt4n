# DINH CHINH DINH NGHIA `omega` CHO LESSON 23.26

Nguon khoa: `A077` muc 3; tai xac nhan boi `A084` muc 2.

Hai file ke hoach `PHASE_23_v3.md` va `MASTER_PLAN_v8.md` khong co trong
workspace tai ngay 2026-08-28. Khi import chung, muc thiet ke 23.26 PHAI dung
nguyen dinh nghia sau thay cho ban amplitude mixing:

```text
rho_l = mu_l + sigma*[sqrt(omega)*(sum_p M[l,p]*f_p)/sqrt(d_l)
                      + sqrt(1-omega)*g_l]

f_p ~ N(0,1) doc lap; g_l ~ N(0,1) doc lap
d_l = so duong dung link l
```

Day la **variance-share parameterization**:

```text
Var(rho_l)=sigma^2 voi moi omega
r_lm(omega)=omega*k_lm
k_lm=c_lm/sqrt(d_l*d_m)
```

Cam ban `omega*path+(1-omega)*link`: no la amplitude-share, cho variance
thay doi va `r(omega)` phi tuyen. Moi generator 23.26 phai qua round-trip test
`structured_matrix(omega) -> omega_contrast == omega` tai 0/.25/.5/1.
