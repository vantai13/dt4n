variable "project_name" {
  description = "Ten project, dung de dat ten EC2/IAM/security group."
  type        = string
  default     = "dt4n"
}

variable "environment" {
  description = "Nhan moi truong, vi du research/dev/prod."
  type        = string
  default     = "research"
}

variable "aws_region" {
  description = "Region AWS. Singapore gan Viet Nam va phu hop ghi chu migration."
  type        = string
  default     = "ap-southeast-1"
}

variable "instance_count" {
  description = "So EC2 doc lap can tao. De 1 cho may chinh; tang len neu muon chay nhieu seed doc lap."
  type        = number
  default     = 1

  validation {
    condition     = var.instance_count >= 1 && var.instance_count <= 5
    error_message = "instance_count nen nam trong khoang 1..5 de tranh tao qua nhieu may dat tien."
  }
}

variable "instance_type" {
  description = "Mac dinh bat dau bang m7i.2xlarge de tiet kiem. Co the resize len m7i.4xlarge khi benchmark/train nang."
  type        = string
  default     = "m7i.2xlarge"
}

variable "root_volume_size_gb" {
  description = "Dung luong root EBS gp3 cho code, Docker image, Ditto/Mongo data va ket qua train."
  type        = number
  default     = 200
}

variable "root_volume_delete_on_termination" {
  description = "false giup giu lai EBS khi terminate EC2, tranh mat du lieu. Luu y van tinh tien EBS."
  type        = bool
  default     = false
}

variable "ssh_public_key_file" {
  description = "Duong dan public key local de tao AWS key pair moi. Chay: ssh-keygen -t ed25519 -f ~/.ssh/dt4n-aws"
  type        = string
  default     = "./dt4n-aws.pub"
}

variable "ssh_private_key_file" {
  description = "Duong dan private key local chi dung de in lenh SSH/rsync. Terraform khong upload file nay."
  type        = string
  default     = "./dt4n-aws.pem"
}

variable "ssh_public_key" {
  description = "Neu khong muon doc tu file, dan noi dung public key vao day. Khong bao gio dan private key."
  type        = string
  default     = ""
  sensitive   = true
}

variable "existing_key_pair_name" {
  description = "Neu da co EC2 key pair tren AWS, dien ten vao day va Terraform se khong tao key pair moi."
  type        = string
  default     = ""
}

variable "ssh_allowed_cidrs" {
  description = "CIDR duoc phep SSH vao EC2. Nen doi thanh IP nha ban dang x.x.x.x/32 truoc khi apply."
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

variable "subnet_id" {
  description = "Tuy chon. De rong de AWS dung default subnet trong default VPC."
  type        = string
  default     = ""
}

variable "allocate_elastic_ip" {
  description = "true de IP khong doi sau khi stop/start. Luu y public IPv4/EIP co tinh phi."
  type        = bool
  default     = true
}

variable "git_repo_url" {
  description = "Repo se clone len EC2 trong cloud-init. Neu repo private hoac muon rsync local, co the de rong."
  type        = string
  default     = "https://github.com/vantai13/dt4n.git"
}

variable "git_branch" {
  description = "Branch clone len EC2."
  type        = string
  default     = "main"
}

variable "create_conda_envs" {
  description = "true de cloud-init tao env fallback. Mac dinh false vi workflow nay restore 2 env Conda hien co tu WSL."
  type        = bool
  default     = false
}

variable "install_dashboard_dependencies" {
  description = "true de chay npm ci trong dashboard neu repo clone thanh cong."
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
