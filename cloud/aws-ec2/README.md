# DT4N EC2 Terraform

Thu muc nay tao Ubuntu EC2 cho DT4N: Ubuntu 22.04, `m7i.2xlarge` mac dinh, EBS gp3 200 GB, Docker, Mininet, Open vSwitch, Node.js va Miniforge. Hai env Conda local `sdn_net` va `sdn_rl` duoc export/restore rieng de EC2 khop WSL hon.

## 1. Chuan bi key va bien

```bash
cd cloud/aws-ec2
cp terraform.tfvars.example terraform.tfvars
```

Neu ban da dat `dt4n-aws.pem` trong thu muc nay:

```bash
chmod 600 dt4n-aws.pem
ssh-keygen -y -f dt4n-aws.pem > dt4n-aws.pub
```

Neu muon tao key moi thay vi dung file `.pem` san co:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/dt4n-aws -C dt4n-aws
```

roi sua `ssh_public_key_file` va `ssh_private_key_file` trong `terraform.tfvars`.

Mo `terraform.tfvars` va sua it nhat:

```hcl
ssh_allowed_cidrs = ["YOUR_PUBLIC_IP/32"]
app_allowed_cidrs = ["YOUR_PUBLIC_IP/32"]
```

Xem IP public hien tai:

```bash
curl https://checkip.amazonaws.com
```

## 2. Tao EC2

```bash
terraform init
terraform fmt
terraform plan
terraform apply
```

Sau `apply`, Terraform se in `ssh_commands` va `bootstrap_log_commands`. Cloud-init co the mat 5-15 phut vi cai Docker, Mininet, OVS, Node.js va Miniforge. Mac dinh no khong tao Conda env moi; env se restore tu export cua WSL.

```bash
ssh -i ./dt4n-aws.pem ubuntu@EC2_IP 'tail -f /var/log/dt4n-bootstrap.log'
```

## 3. Setup VS Code Remote SSH

Codex da copy key vao Windows va tao host `dt4n-aws` trong:

```text
C:\Users\VAN TAI\.ssh\config
```

Sau khi `terraform apply` co IP that, update SSH config cho VS Code:

```bash
./scripts/setup-vscode-ssh-from-terraform.sh
```

Sau do trong VS Code Windows:

```text
Ctrl + Shift + P -> Remote-SSH: Connect to Host... -> dt4n-aws
```

Huong dan chi tiet nam o `VSCODE_REMOTE_SSH.md`.

## 4. Export Conda env tu WSL

Da co script export 2 env local cua ban:

```bash
./scripts/export-conda-envs.sh
```

Ket qua nam trong `conda-envs/`:

```text
sdn_net-full.yml
sdn_net-minimal.yml
sdn_net-pip.txt
sdn_rl-full.yml
sdn_rl-minimal.yml
sdn_rl-pip.txt
```

Day la cach nen dung truoc vi nhe. Neu muon copy gan nhu nguyen binary env, co the dung:

```bash
./scripts/pack-conda-envs.sh
```

Luu y `conda-pack` tao file `.tar.gz` lon, khong phu hop neu WSL dang qua it dung luong.

## 5. Dong bo code hien tai tu WSL len EC2

Cloud-init co clone repo GitHub, nhung cac file local chua commit se khong co tren EC2. De copy source hien tai, gom `ditto/` va controller Ryu trong `mininet/`:

```bash
./scripts/sync-project.sh ubuntu@EC2_IP ./dt4n-aws.pem /home/ubuntu/dt4n
```

Mac dinh script khong copy `.env`, key, `runs/`, `node_modules/`, `.terraform/`. Neu muon copy ca ket qua train:

```bash
INCLUDE_RUNS=1 ./scripts/sync-project.sh ubuntu@EC2_IP ./dt4n-aws.pem /home/ubuntu/dt4n
```

## 6. Restore Conda env tren EC2

Sau khi sync project:

```bash
ssh -i ./dt4n-aws.pem ubuntu@EC2_IP
cd ~/dt4n
./cloud/aws-ec2/scripts/restore-conda-envs.sh
```

Neu da dung `pack-conda-envs.sh` thay vi export YAML:

```bash
./cloud/aws-ec2/scripts/unpack-conda-packs.sh
```

## 7. Kiem tra nhanh may EC2

```bash
./scripts/check-remote.sh ubuntu@EC2_IP ./dt4n-aws.pem
```

Tren EC2:

```bash
cd ~/dt4n
source ~/miniforge3/etc/profile.d/conda.sh
conda activate sdn_rl
PYTHONPATH=$PWD python -m pytest test -q
```

## 8. Chay DT4N co ban

Khi ban da restore Ditto Docker Compose/.env rieng, chay Ditto truoc:

```bash
docker compose up -d
```

Terminal Ryu:

```bash
cd ~/dt4n
source ~/miniforge3/etc/profile.d/conda.sh
conda activate sdn_net
PYTHONPATH=$PWD ryu-manager mininet.controller_static --ofp-tcp-listen-port 6653
```

Terminal Mininet/sync:

```bash
cd ~/dt4n
source ~/miniforge3/etc/profile.d/conda.sh
conda activate sdn_rl
sudo -E env PYTHONPATH=$PWD PATH=$PATH python -m mininet.run_sync
```

## 9. Ghi chu quan trong

- Khong dua mat khau ca nhan vao Terraform. Terraform state co the luu plaintext.
- File `dt4n-aws.pem` la private key, da nam trong `.gitignore`; khong commit file nay.
- `root_volume_delete_on_termination = false` giup tranh mat du lieu khi terminate, nhung EBS van tinh phi cho den khi xoa volume.
- `m7i.2xlarge` la diem bat dau hop ly. Khi benchmark/train nang, stop instance roi doi `instance_type = "m7i.4xlarge"` va apply lai.
- `instance_count` co the tang len 2-3 de chay nhieu seed, moi may la mot full DT4N stack doc lap.
- Security group mac dinh trong file mau dang mo ra internet de de thu. Truoc khi apply that, nen khoa ve IP cua ban bang `/32`.
