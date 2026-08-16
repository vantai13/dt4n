# DT4N GCP Compute Terraform

Thu muc nay tao Ubuntu 22.04 VM tren Google Compute Engine cho DT4N, tuong duong module AWS EC2: `n2-standard-8` mac dinh, boot disk `pd-balanced` 200 GB, Docker, Mininet, Open vSwitch, Node.js va Miniforge. Code duoc clone trong startup script, sau do co the rsync source local de mang theo cac thay doi chua commit.

## 1. Chuan bi Google Cloud

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_GCP_PROJECT_ID
gcloud services enable compute.googleapis.com --project YOUR_GCP_PROJECT_ID
```

Neu dung service account JSON thay vi login user:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

## 2. Chuan bi key va bien

```bash
cd cloud/gcp-compute
./scripts/prepare-local.sh YOUR_GCP_PROJECT_ID
```

Script nay se tao `terraform.tfvars`, tao key `dt4n-gcp.pem` neu chua co, va khoa firewall ve IP public hien tai cua ban. Neu muon lam tay:

```bash
cp terraform.tfvars.example terraform.tfvars
ssh-keygen -t ed25519 -f ./dt4n-gcp.pem -C dt4n-gcp
chmod 600 ./dt4n-gcp.pem
```

Sau do mo `terraform.tfvars` va sua it nhat:

```hcl
gcp_project_id    = "YOUR_GCP_PROJECT_ID"
ssh_allowed_cidrs = ["YOUR_PUBLIC_IP/32"]
app_allowed_cidrs = ["YOUR_PUBLIC_IP/32"]
```

Xem IP public hien tai:

```bash
curl https://checkip.amazonaws.com
```

## 3. Tao VM

Nhanh nhat:

```bash
./scripts/apply-and-check.sh
```

Script nay chay `terraform init/validate/apply`, lay IP, doi SSH, doi startup script tao `~/DT4N_GCP_READY.txt`, roi chay `scripts/check-remote.sh`.

Neu muon chay tung buoc:

```bash
terraform init
terraform fmt
terraform plan
terraform apply
```

Sau `apply`, Terraform se in `ssh_commands` va `bootstrap_log_commands`. Startup script co the mat 5-15 phut vi cai Docker, Mininet, OVS, Node.js va Miniforge.

```bash
ssh -i ./dt4n-gcp.pem ubuntu@GCE_IP 'tail -f /var/log/dt4n-bootstrap.log'
```

## 4. Dong bo code local len VM

Startup script co clone GitHub, nhung cac file local chua commit se khong co tren VM. De copy source hien tai:

```bash
./scripts/sync-project.sh ubuntu@GCE_IP ./dt4n-gcp.pem /home/ubuntu/dt4n
```

Mac dinh script khong copy `.env`, key, `runs/`, `node_modules/`, `.terraform/`. Neu muon copy ca ket qua train:

```bash
INCLUDE_RUNS=1 ./scripts/sync-project.sh ubuntu@GCE_IP ./dt4n-gcp.pem /home/ubuntu/dt4n
```

## 5. Dong bo Ditto deployment hien tai

May local dang dung checkout Eclipse Ditto rieng o `~/tools/ditto`. Vi checkout nay co the co sua `deployment/docker/docker-compose.yml`, `nginx.conf`, `nginx.htpasswd`, script rieng se sync no len VM va so sanh SHA-256 cua `deployment/docker/*` de dam bao GCP khop dung may hien tai:

```bash
./scripts/sync-ditto-deployment.sh ubuntu@GCE_IP ./dt4n-gcp.pem /home/ubuntu/tools/ditto
```

Neu muon sync xong va cap nhat stack Ditto dang chay, nen clean restart de Pekko cluster khong giu member cu:

```bash
START_DITTO=1 CLEAN_DITTO=1 COMPOSE_PROJECT=dt4n-aoi-smoke DITTO_VERSION=3.9.1 \
  ./scripts/sync-ditto-deployment.sh ubuntu@GCE_IP ./dt4n-gcp.pem /home/ubuntu/tools/ditto
```

Neu muon dung y default cua may local, bo `DITTO_VERSION`; compose se dung `${DITTO_VERSION:-latest}` trong file cua Ditto.

## 6. Restore Conda env tren VM

Neu da co export env trong `cloud/gcp-compute/conda-envs`, script se dung no. Neu chua co, script fallback sang export cu trong `cloud/aws-ec2/conda-envs`.

```bash
ssh -i ./dt4n-gcp.pem ubuntu@GCE_IP
cd ~/dt4n
./cloud/gcp-compute/scripts/restore-conda-envs.sh
```

Mac dinh GCP restore bang `*-minimal.yml` roi cai pip requirements da loc CUDA/NVIDIA de phu hop VM CPU. Neu that su muon thu full export goc:

```bash
PREFER_MINIMAL=0 ./cloud/gcp-compute/scripts/restore-conda-envs.sh
```

Muon export lai env tu WSL sang thu muc GCP:

```bash
./scripts/export-conda-envs.sh
```

## 7. Kiem tra nhanh

```bash
./scripts/check-remote.sh ubuntu@GCE_IP ./dt4n-gcp.pem
```

Tren VM:

```bash
cd ~/dt4n
source ~/miniforge3/etc/profile.d/conda.sh
conda activate sdn_rl
PYTHONPATH=$PWD python -m pytest test -q
```

## 8. VS Code Remote SSH

Trong WSL tren Windows, sau khi `terraform apply` co IP:

```bash
./scripts/setup-vscode-ssh-from-terraform.sh
```

Script tao host `dt4n-gcp` trong Windows SSH config. Sau do mo VS Code:

```text
Ctrl + Shift + P -> Remote-SSH: Connect to Host... -> dt4n-gcp
```

## 9. Ghi chu quan trong

- Khong dua password, token, service account JSON vao Terraform. Terraform state co the luu plaintext.
- File `dt4n-gcp.pem` la private key, da nam trong `.gitignore`; khong commit file nay.
- `boot_disk_auto_delete = false` giup tranh mat du lieu khi xoa VM, nhung disk van tinh phi cho den khi xoa disk.
- `reserve_static_ip = true` giu IP on dinh hon, nhung reserved external IP co the tinh phi khi khong gan vao VM dang chay.
- Firewall trong file mau nen khoa ve IP cua ban bang `/32` truoc khi apply that.
- `n2-standard-8` la diem bat dau hop ly. Khi benchmark/train nang, stop VM roi doi `machine_type = "n2-standard-16"` va apply lai.
