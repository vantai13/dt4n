locals {
  name_prefix = "${var.project_name}-${var.environment}"

  # Khong dua password ca nhan vao Terraform. Terraform state co the luu plaintext.
  # SSH dung key pair; secret runtime nen de trong .env rieng, SSM Parameter Store hoac Secrets Manager.
  ssh_public_key_material = trimspace(
    var.ssh_public_key != "" ? var.ssh_public_key : try(file(pathexpand(var.ssh_public_key_file)), "")
  )

  key_pair_name = var.existing_key_pair_name != "" ? var.existing_key_pair_name : aws_key_pair.dt4n[0].key_name

  user_data = templatefile("${path.module}/user-data.sh.tftpl", {
    project_name                   = var.project_name
    git_repo_url                   = var.git_repo_url
    git_branch                     = var.git_branch
    create_conda_envs              = var.create_conda_envs ? "true" : "false"
    install_dashboard_dependencies = var.install_dashboard_dependencies ? "true" : "false"
    ryu_conda_env_name             = var.ryu_conda_env_name
    rl_conda_env_name              = var.rl_conda_env_name
  })
}

data "aws_vpc" "default" {
  default = true
}

data "aws_ami" "ubuntu_2204" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }

  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_key_pair" "dt4n" {
  count = var.existing_key_pair_name == "" ? 1 : 0

  key_name   = "${local.name_prefix}-key"
  public_key = local.ssh_public_key_material

  tags = {
    Name = "${local.name_prefix}-key"
  }

  lifecycle {
    precondition {
      condition     = local.ssh_public_key_material != ""
      error_message = "Chua co SSH public key. Hay chay: ssh-keygen -t ed25519 -f ~/.ssh/dt4n-aws -C dt4n-aws, hoac dien existing_key_pair_name."
    }
  }
}

resource "aws_security_group" "dt4n" {
  name_prefix = "${local.name_prefix}-"
  description = "DT4N EC2 access: SSH plus selected app ports"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.ssh_allowed_cidrs
  }

  dynamic "ingress" {
    for_each = toset(var.public_app_ports)

    content {
      description = "DT4N public app port ${ingress.value}"
      from_port   = ingress.value
      to_port     = ingress.value
      protocol    = "tcp"
      cidr_blocks = var.app_allowed_cidrs
    }
  }

  egress {
    description = "Outbound internet for apt/docker/pip/npm"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.name_prefix}-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_iam_role" "ssm" {
  name = "${local.name_prefix}-ssm-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.ssm.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "ssm" {
  name = "${local.name_prefix}-instance-profile"
  role = aws_iam_role.ssm.name
}

resource "aws_instance" "dt4n" {
  count = var.instance_count

  ami                         = data.aws_ami.ubuntu_2204.id
  instance_type               = var.instance_type
  key_name                    = local.key_pair_name
  iam_instance_profile        = aws_iam_instance_profile.ssm.name
  vpc_security_group_ids      = [aws_security_group.dt4n.id]
  subnet_id                   = var.subnet_id != "" ? var.subnet_id : null
  associate_public_ip_address = true
  user_data                   = local.user_data
  user_data_replace_on_change = true

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 2
  }

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.root_volume_size_gb
    iops                  = 3000
    throughput            = 125
    encrypted             = true
    delete_on_termination = var.root_volume_delete_on_termination

    tags = {
      Name = format("%s-root-%02d", local.name_prefix, count.index + 1)
    }
  }

  tags = {
    Name = format("%s-%02d", local.name_prefix, count.index + 1)
    Role = "dt4n-full-stack-worker"
  }

  lifecycle {
    # AMI moi xuat hien lien tuc; tranh viec terraform plan doi recreate may dang dung.
    # Khi muon rebuild OS bang AMI moi, hay tao instance moi hoac taint resource co chu dich.
    ignore_changes = [ami]
  }
}

resource "aws_eip" "dt4n" {
  count = var.allocate_elastic_ip ? var.instance_count : 0

  domain   = "vpc"
  instance = aws_instance.dt4n[count.index].id

  tags = {
    Name = format("%s-eip-%02d", local.name_prefix, count.index + 1)
  }
}
