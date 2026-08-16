locals {
  raw_name_prefix       = lower(replace("${var.project_name}-${var.environment}", "/[^a-z0-9-]/", "-"))
  name_prefix_unclipped = trim(local.raw_name_prefix, "-")
  name_prefix           = substr(local.name_prefix_unclipped != "" ? local.name_prefix_unclipped : "dt4n", 0, 45)

  label_project_raw     = trim(lower(replace(var.project_name, "/[^a-z0-9_-]/", "_")), "_")
  label_environment_raw = trim(lower(replace(var.environment, "/[^a-z0-9_-]/", "_")), "_")
  label_project         = substr(local.label_project_raw != "" ? local.label_project_raw : "dt4n", 0, 63)
  label_environment     = substr(local.label_environment_raw != "" ? local.label_environment_raw : "research", 0, 63)

  network_tag = "${local.name_prefix}-vm"

  ssh_public_key_material = trimspace(
    var.ssh_public_key != "" ? var.ssh_public_key : try(file(pathexpand(var.ssh_public_key_file)), "")
  )

  startup_script = templatefile("${path.module}/user-data.sh.tftpl", {
    project_name                   = var.project_name
    git_repo_url                   = var.git_repo_url
    git_branch                     = var.git_branch
    create_conda_envs              = var.create_conda_envs ? "true" : "false"
    install_dashboard_dependencies = var.install_dashboard_dependencies ? "true" : "false"
    install_ai_cli_tools           = var.install_ai_cli_tools ? "true" : "false"
    ryu_conda_env_name             = var.ryu_conda_env_name
    rl_conda_env_name              = var.rl_conda_env_name
    ssh_username                   = var.ssh_username
  })
}

data "google_compute_image" "ubuntu_2204" {
  family  = "ubuntu-2204-lts"
  project = "ubuntu-os-cloud"
}

resource "google_compute_network" "dt4n" {
  name                    = "${local.name_prefix}-net"
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
}

resource "google_compute_subnetwork" "dt4n" {
  name          = "${local.name_prefix}-subnet"
  ip_cidr_range = var.subnet_cidr
  region        = var.gcp_region
  network       = google_compute_network.dt4n.self_link
}

resource "google_compute_firewall" "ssh" {
  name      = "${local.name_prefix}-allow-ssh"
  network   = google_compute_network.dt4n.self_link
  direction = "INGRESS"
  priority  = 1000

  target_tags   = [local.network_tag]
  source_ranges = var.ssh_allowed_cidrs

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
}

resource "google_compute_firewall" "apps" {
  count = length(var.public_app_ports) > 0 ? 1 : 0

  name      = "${local.name_prefix}-allow-apps"
  network   = google_compute_network.dt4n.self_link
  direction = "INGRESS"
  priority  = 1010

  target_tags   = [local.network_tag]
  source_ranges = var.app_allowed_cidrs

  allow {
    protocol = "tcp"
    ports    = [for port in var.public_app_ports : tostring(port)]
  }
}

resource "google_compute_address" "dt4n" {
  count = var.reserve_static_ip ? var.instance_count : 0

  name   = format("%s-ip-%02d", local.name_prefix, count.index + 1)
  region = var.gcp_region
}

resource "google_compute_instance" "dt4n" {
  count = var.instance_count

  name                      = format("%s-%02d", local.name_prefix, count.index + 1)
  machine_type              = var.machine_type
  zone                      = var.gcp_zone
  can_ip_forward            = var.can_ip_forward
  allow_stopping_for_update = true
  deletion_protection       = var.deletion_protection
  tags                      = [local.network_tag]

  labels = {
    project     = local.label_project
    environment = local.label_environment
    role        = "dt4n_worker"
  }

  boot_disk {
    auto_delete = var.boot_disk_auto_delete

    initialize_params {
      image = data.google_compute_image.ubuntu_2204.self_link
      size  = var.boot_disk_size_gb
      type  = var.boot_disk_type

      labels = {
        project     = local.label_project
        environment = local.label_environment
      }
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.dt4n.self_link

    access_config {
      nat_ip = var.reserve_static_ip ? google_compute_address.dt4n[count.index].address : null
    }
  }

  metadata = {
    block-project-ssh-keys = "true"
    enable-oslogin         = "FALSE"
    ssh-keys               = "${var.ssh_username}:${local.ssh_public_key_material}"
  }

  metadata_startup_script = local.startup_script

  lifecycle {
    precondition {
      condition     = local.ssh_public_key_material != ""
      error_message = "Chua co SSH public key. Hay chay: ssh-keygen -t ed25519 -f ./dt4n-gcp.pem -C dt4n-gcp, hoac dien ssh_public_key."
    }
  }
}
