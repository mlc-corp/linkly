variable "gcp_project_id" {
  description = "El ID de tu proyecto de GCP."
  type        = string
}

variable "gcp_region" {
  description = "La región donde desplegar los servicios (ej. us-central1)."
  type        = string
  default     = "us-central1"
}

variable "docker_hub_user" {
  description = "Tu nombre de usuario de Docker Hub."
  type        = string
}