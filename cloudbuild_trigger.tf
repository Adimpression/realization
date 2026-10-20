terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0.0"
    }
  }
}

provider "google" {
  project = "tough-transport-214713"
}

variable "github_owner" {
  description = "GitHub organization that owns the source repository."
  type        = string
  default     = "Adimpression"
}

variable "github_repository" {
  description = "GitHub repository monitored by Cloud Build."
  type        = string
  default     = "realization"
}

variable "trigger_branch_regex" {
  description = "Branches that invoke the deterministic qualification build."
  type        = string
  default     = "^main$"
}

resource "google_cloudbuild_trigger" "build" {
  project     = "tough-transport-214713"
  name        = "realization-github"
  description = "Runs the Realized architecture ratchet and deterministic trial BDD."

  filename = "cloudbuild.yaml"

  github {
    owner = var.github_owner
    name  = var.github_repository

    push {
      branch = var.trigger_branch_regex
    }
  }

  included_files = [
    "**",
  ]

  lifecycle {
    prevent_destroy = true
  }
}
