terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id != "" ? var.gcp_project_id : null
  region  = var.gcp_region
  zone    = var.gcp_zone

  default_labels = {
    project     = local.label_project
    environment = local.label_environment
    managed_by  = "terraform"
    owner       = "dt4n"
  }
}
