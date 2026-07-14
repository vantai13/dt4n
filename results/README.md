# Results

Thu muc nay gom artifact do luong va training. Moi thu muc con gan voi mot loai
cau hoi nghien cuu rieng, de tranh tron so do A2 moi voi artifact Phase 5 cu.

## Thu Muc

- `delta/`: thoi gian tu hanh dong/doi bandwidth den khi he qua quan sat on dinh.
- `noise/`: nhieu nen cua state; dung de lap nguong 3-sigma.
- `aoi/`: Age of Information cua Thing trong Ditto/twin.
- `fidelity/`: sai khac giua gia tri that va gia tri twin, gom ca phan tich staleness.
- `train/`: ket qua train/eval va checkpoint agent.
- `baseline/`: diagnostic va baseline chinh sach/rule/oracle/reset.

## Quy Uoc

- File co hau to `_a2` la artifact moi cho A2 9 chieu.
- File khong co hau to `_a2` phan lon la artifact Phase 5/legacy, giu de doi
  chieu lich su.
- JSON nen doc bang:

```bash
python3 -m json.tool results/<group>/<file>.json | less
```

## Thu Tu Chay De Xay Nen So Lieu A2

1. `delta`: chot `delta_s` hop ly.
2. `noise`: chot nguong nhieu nen 3-sigma.
3. `aoi`: biet twin/Ditto cu bao nhieu.
4. `fidelity`: tach sai-vi-cu khoi sai-vi-loi.
5. `train`: train/eval agent voi cac tham so da chot.
