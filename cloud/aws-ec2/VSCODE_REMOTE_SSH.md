# VS Code Remote SSH cho DT4N EC2

Trang nay la quy trinh dung VS Code tren Windows de mo workspace `/home/ubuntu/dt4n` tren EC2.

## Trang thai da setup san

Codex da lam san:

- Copy private key vao Windows: `C:\Users\VAN TAI\.ssh\dt4n-aws.pem`
- Tao SSH config Windows: `C:\Users\VAN TAI\.ssh\config`
- Them host Remote SSH: `dt4n-aws`
- Tao script update IP sau Terraform: `./scripts/setup-vscode-ssh-from-terraform.sh`

Hien tai `HostName` dang la placeholder vi EC2 chua duoc tao:

```ssh
Host dt4n-aws
    HostName REPLACE_WITH_EC2_PUBLIC_IP
```

Sau khi `terraform apply` xong, chay script update IP that.

## 1. Tao EC2 bang Terraform

Trong WSL:

```bash
cd /home/vantai/dt4n/cloud/aws-ec2
terraform init
terraform plan
terraform apply
```

Khi Terraform hoi:

```text
Do you want to perform these actions?
```

go:

```text
yes
```

## 2. Update SSH config cho VS Code

Sau khi `terraform apply` xong va co `public_ips`, chay:

```bash
cd /home/vantai/dt4n/cloud/aws-ec2
./scripts/setup-vscode-ssh-from-terraform.sh
```

Script nay se doc IP tu Terraform output va sua:

```text
C:\Users\VAN TAI\.ssh\config
```

Neu ban muon truyen IP thu cong:

```bash
./scripts/setup-vscode-ssh-from-terraform.sh EC2_PUBLIC_IP
```

## 3. Test SSH truoc

Tu WSL:

```bash
powershell.exe -NoProfile -Command "ssh dt4n-aws hostname"
```

Hoac mo PowerShell Windows va chay:

```powershell
ssh dt4n-aws
```

Lan dau neu hoi:

```text
Are you sure you want to continue connecting?
```

go:

```text
yes
```

Neu vao duoc terminal `ubuntu@ip-...`, thoat bang:

```bash
exit
```

## 4. Ket noi bang VS Code

Trong VS Code tren Windows:

1. Nhan `Ctrl + Shift + P`
2. Chon `Remote-SSH: Connect to Host...`
3. Chon `dt4n-aws`
4. Neu hoi platform, chon `Linux`
5. Doi VS Code cai VS Code Server tren EC2

Khi ket noi thanh cong, goc duoi trai VS Code se hien:

```text
SSH: dt4n-aws
```

## 5. Mo folder DT4N tren EC2

Trong cua so VS Code dang ket noi `SSH: dt4n-aws`:

```text
File -> Open Folder...
```

Nhap:

```text
/home/ubuntu/dt4n
```

Neu folder chua co code, quay lai WSL va sync:

```bash
cd /home/vantai/dt4n/cloud/aws-ec2
./scripts/sync-project.sh ubuntu@EC2_IP ./dt4n-aws.pem /home/ubuntu/dt4n
```

## 6. Restore Conda env tren EC2

Trong terminal VS Code remote:

```bash
cd ~/dt4n
./cloud/aws-ec2/scripts/restore-conda-envs.sh
```

Kiem tra:

```bash
source ~/miniforge3/etc/profile.d/conda.sh
conda env list
```

Phai thay:

```text
sdn_net
sdn_rl
```

## 7. Chon Python interpreter trong VS Code

Trong cua so Remote SSH:

```text
Ctrl + Shift + P -> Python: Select Interpreter
```

Chon:

```text
/home/ubuntu/miniforge3/envs/sdn_rl/bin/python
```

Neu can chay Ryu/controller thi dung:

```text
/home/ubuntu/miniforge3/envs/sdn_net/bin/python
```

## 8. Port forwarding dashboard/Ditto

Trong VS Code Remote SSH:

```text
View -> Ports
```

Forward cac port hay dung:

```text
8080  Ditto nginx
8081  Ditto gateway neu can
5173  Vite dashboard
```

Sau do mo tren trinh duyet Windows:

```text
http://localhost:8080
http://localhost:5173
```

## 9. Cach biet minh dang o EC2

Trong terminal VS Code:

```bash
hostname
whoami
pwd
```

Dung thi se gan nhu:

```text
ip-172-31-...
ubuntu
/home/ubuntu/dt4n
```

Khong phai:

```text
/home/vantai/dt4n
```

## 10. Khi IP thay doi

Vi Terraform dang de `allocate_elastic_ip = true`, IP se co dinh hon sau stop/start. Neu ban tat EIP hoac IP bi doi, chay lai:

```bash
cd /home/vantai/dt4n/cloud/aws-ec2
./scripts/setup-vscode-ssh-from-terraform.sh
```
