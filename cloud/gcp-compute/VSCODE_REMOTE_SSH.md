# VS Code Remote SSH cho DT4N GCP

Trang nay la quy trinh dung VS Code tren Windows de mo workspace `/home/ubuntu/dt4n` tren Google Compute Engine, tuong tu flow EC2 cu.

## Trang thai da setup san

Codex da lam san cho VM hien tai:

- Tao VM GCP bang Terraform: `dt4n-research-01`
- Public IP lay tu Terraform output: `terraform output public_ips`
- Tao private key local: `/home/vantai/dt4n/cloud/gcp-compute/dt4n-gcp.pem`
- Tao script update IP sau Terraform: `./scripts/setup-vscode-ssh-from-terraform.sh`
- Cai san tren VM: Docker, OVS, Mininet, Node.js, Miniforge, `sdn_net`, `sdn_rl`, Codex CLI, Claude Code CLI

Sau khi chay script setup Windows SSH, host Remote SSH se la:

```ssh
Host dt4n-gcp
    HostName GCE_IP
    User ubuntu
```

## 1. Tao hoac cap nhat VM bang Terraform

Trong WSL:

```bash
cd /home/vantai/dt4n/cloud/gcp-compute
terraform init
terraform plan
terraform apply
```

Neu tao moi tu dau:

```bash
./scripts/prepare-local.sh YOUR_GCP_PROJECT_ID
./scripts/apply-and-check.sh
```

## 2. Update SSH config cho VS Code

Sau khi `terraform apply` co IP, chay:

```bash
cd /home/vantai/dt4n/cloud/gcp-compute
./scripts/setup-vscode-ssh-from-terraform.sh
```

Script nay se doc IP tu Terraform output va sua:

```text
C:\Users\VAN TAI\.ssh\config
```

Neu muon truyen IP thu cong:

```bash
./scripts/setup-vscode-ssh-from-terraform.sh GCE_IP
```

## 3. Test SSH truoc

Tu WSL:

```bash
powershell.exe -NoProfile -Command "ssh dt4n-gcp hostname"
```

Hoac mo PowerShell Windows va chay:

```powershell
ssh dt4n-gcp
```

Neu vao duoc terminal `ubuntu@dt4n-research-01`, thoat bang:

```bash
exit
```

## 4. Ket noi bang VS Code

Trong VS Code tren Windows:

1. Nhan `Ctrl + Shift + P`
2. Chon `Remote-SSH: Connect to Host...`
3. Chon `dt4n-gcp`
4. Neu hoi platform, chon `Linux`
5. Doi VS Code cai VS Code Server tren GCP VM

Khi ket noi thanh cong, goc duoi trai VS Code se hien:

```text
SSH: dt4n-gcp
```

## 5. Mo folder DT4N tren GCP VM

Trong cua so VS Code dang ket noi `SSH: dt4n-gcp`:

```text
File -> Open Folder...
```

Nhap:

```text
/home/ubuntu/dt4n
```

Neu can sync lai source local:

```bash
cd /home/vantai/dt4n/cloud/gcp-compute
./scripts/sync-project.sh ubuntu@GCE_IP ./dt4n-gcp.pem /home/ubuntu/dt4n
```

## 6. Kiem tra Codex va Claude Code trong VS Code terminal

Trong terminal VS Code remote:

```bash
cd ~/dt4n
codex --version
claude --version
```

Lan dau chay interactive, dang nhap rieng tung tool:

```bash
codex
claude
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

## 9. Khi IP thay doi

Vi Terraform dang de `reserve_static_ip = true`, IP se on dinh hon sau stop/start. Neu IP doi, chay lai:

```bash
cd /home/vantai/dt4n/cloud/gcp-compute
./scripts/setup-vscode-ssh-from-terraform.sh
```
