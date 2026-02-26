terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.31"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_container_cluster" "autopilot" {
  name     = var.cluster_name
  location = var.region

  enable_autopilot = true
}

resource "google_service_account" "iam_collector" {
  account_id   = var.gcp_service_account_name
  display_name = "IAM Evidence Collector Service Account"
}

resource "google_project_iam_member" "collector_project_role" {
  project = var.project_id
  role    = var.gcp_service_account_role
  member  = "serviceAccount:${google_service_account.iam_collector.email}"
}

data "google_client_config" "default" {}

provider "kubernetes" {
  host                   = "https://${google_container_cluster.autopilot.endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(google_container_cluster.autopilot.master_auth[0].cluster_ca_certificate)
}

resource "kubernetes_namespace" "iam_evidence" {
  metadata {
    name = var.namespace
  }
}

resource "kubernetes_service_account" "iam_collector" {
  metadata {
    name      = var.k8s_service_account_name
    namespace = kubernetes_namespace.iam_evidence.metadata[0].name
    annotations = {
      "iam.gke.io/gcp-service-account" = google_service_account.iam_collector.email
    }
  }
}

resource "google_service_account_iam_binding" "workload_identity" {
  service_account_id = google_service_account.iam_collector.name
  role               = "roles/iam.workloadIdentityUser"
  members = [
    "serviceAccount:${var.project_id}.svc.id.goog[${var.namespace}/${var.k8s_service_account_name}]"
  ]
}
