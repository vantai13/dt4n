variable "project_name" {
  description = "Ten project, dung de dat ten VM/network/firewall."
  type        = string
  default     = "dt4n"
}

variable "environment" {
  description = "Nhan moi truong, vi du research/dev/prod."
  type        = string
  default     = "research"
}

variable "gcp_project_id" {
  description = "Google Cloud project ID. De rong neu muon provider lay tu ADC/gcloud config, nhung nen dien ro."
  type        = string
  default     = ""
}

variable "gcp_region" {
  description = "Region GCP. asia-southeast1 la Singapore, gan Viet Nam."
  type        = string
  default     = "asia-southeast1"
}

variable "gcp_zone" {
  description = "Zone GCP trong region da chon."
  type        = string
  default     = "asia-southeast1-b"
}

variable "instance_count" {
  description = "So VM doc lap can tao. De 1 cho may chinh; tang len neu muon chay nhieu seed doc lap."
  type        = number
  default     = 1

  validation {
    condition     = var.instance_count >= 1 && var.instance_count <= 5
    error_message = "instance_count nen nam trong khoang 1..5 de tranh tao qua nhieu VM dat tien."
  }
}

variable "machine_type" {
  description = "Mac dinh gan voi m7i.2xlarge: 8 vCPU, 32 GB RAM. Co the doi sang n2-standard-16 khi can nang hon."
  type        = string
  default     = "n2-standard-8"
}

variable "boot_disk_size_gb" {
  description = "Dung luong boot disk cho code, Docker image, Ditto/Mongo data va ket qua train."
  type        = number
  default     = 200
}

variable "boot_disk_type" {
  description = "Loai persistent disk. pd-balanced la diem bat dau hop ly gan voi gp3."
  type        = string
  default     = "pd-balanced"
}

variable "boot_disk_auto_delete" {
  description = "false giup giu lai disk khi xoa VM, tranh mat du lieu. Luu y disk van tinh phi."
  type        = bool
  default     = false
}

variable "deletion_protection" {
  description = "Bat khoa xoa VM ngoai y muon. De false cho workflow thu nghiem Terraform destroy gon."
  type        = bool
  default     = false
}

variable "reserve_static_ip" {
  description = "true de public IP co dinh hon sau stop/start, tuong tu Elastic IP. IP khong dung co the tinh phi."
  type        = bool
  default     = true
}

variable "ssh_username" {
  description = "Linux user de SSH vao VM. Startup script se tao user neu image chua co."
  type        = string
  default     = "ubuntu"
}

variable "ssh_public_key_file" {
  description = "Duong dan public key local de dua vao GCE metadata. Chay: ssh-keygen -t ed25519 -f ./dt4n-gcp.pem -C dt4n-gcp"
  type        = string
  default     = "./dt4n-gcp.pem.pub"
}

variable "ssh_private_key_file" {
  description = "Duong dan private key local chi dung de in lenh SSH/rsync. Terraform khong upload file nay."
  type        = string
  default     = "./dt4n-gcp.pem"
}

variable "ssh_public_key" {
  description = "Neu khong muon doc tu file, dan noi dung public key vao day. Khong bao gio dan private key."
  type        = string
  default     = ""
  sensitive   = true
}

variable "ssh_allowed_cidrs" {
  description = "CIDR duoc phep SSH vao VM. Nen doi thanh IP nha ban dang x.x.x.x/32 truoc khi apply."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "app_allowed_cidrs" {
  description = "CIDR duoc phep truy cap dashboard/Ditto demo ports. Nen gioi han IP ca nhan."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "public_app_ports" {
  description = "Cac port public tam thoi cho DT4N: 80 nginx, 8080 Ditto nginx, 5173 Vite dashboard."
  type        = list(number)
  default     = [80, 8080, 5173]
}

variable "subnet_cidr" {
  description = "CIDR cho subnet rieng cua DT4N trong GCP."
  type        = string
  default     = "10.42.0.0/24"
}

variable "can_ip_forward" {
  description = "Cho phep VM forward packet o muc GCE. Thuong khong can cho Mininet noi bo, nhung bat san cho lab SDN."
  type        = bool
  default     = true
}

variable "git_repo_url" {
  description = "Repo se clone len VM trong startup script. Neu repo private hoac muon rsync local, co the de rong."
  type        = string
  default     = "https://github.com/vantai13/dt4n.git"
}

variable "git_branch" {
  description = "Branch clone len VM."
  type        = string
  default     = "main"
}

variable "create_conda_envs" {
  description = "true de startup script tao env fallback. Mac dinh false vi workflow nay restore 2 env Conda hien co tu WSL."
  type        = bool
  default     = false
}

variable "install_dashboard_dependencies" {
  description = "true de chay npm ci trong dashboard neu repo clone thanh cong."
  type        = bool
  default     = true
}

variable "install_ai_cli_tools" {
  description = "true de cai Codex CLI va Claude Code CLI cho user SSH tren VM."
  type        = bool
  default     = true
}

variable "ryu_conda_env_name" {
  description = "Ten Conda env cho Ryu/controller. Khop voi env local hien tai cua ban."
  type        = string
  default     = "sdn_net"
}

variable "rl_conda_env_name" {
  description = "Ten Conda env cho RL/measurements. Khop voi env local hien tai cua ban."
  type        = string
  default     = "sdn_rl"
}
