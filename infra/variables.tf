variable "project_id" {
  description = "GCP project ID where resources will be created."
  type        = string
  default = "gcp-iam-evidence-collector"
}

variable "region" {
  description = "Region for the GKE Autopilot cluster."
  type        = string
  default     = "us-central1"
}

variable "cluster_name" {
  description = "Name of the GKE cluster."
  type        = string
  default     = "iam-evidence-cluster"
}

variable "namespace" {
  description = "Kubernetes namespace for the CronJob and service account."
  type        = string
  default     = "iam-evidence"
}

variable "k8s_service_account_name" {
  description = "Kubernetes Service Account name used by the CronJob."
  type        = string
  default     = "iam-collector-sa"
}

variable "gcp_service_account_name" {
  description = "GCP Service Account account_id."
  type        = string
  default     = "iam-collector-sa"
}

variable "gcp_service_account_role" {
  description = "Project role granted to the collector GCP Service Account."
  type        = string
  default     = "roles/resourcemanager.projectIamAdmin"
}
