# Configura el proveedor de Google Cloud
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      # ACTUALIZADO: Usamos la última versión mayor (7.x)
      version = "~> 7.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# 1. Habilitar las APIs necesarias
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",       # Para Cloud Run
    "firestore.googleapis.com", # Para Firestore
    "iam.googleapis.com"        # Para Cuentas de Servicio y permisos
  ])
  service            = each.key
  disable_on_destroy = false
}

# 2. Crear la base de datos Firestore
# (Depende de que la API de Firestore esté activa)
resource "google_firestore_database" "database" {
  provider        = google
  project         = var.gcp_project_id
  name            = "(default)"
  location_id     = var.gcp_region
  
  type            = "FIRESTORE_NATIVE" 

  depends_on = [
    google_project_service.apis["firestore.googleapis.com"]
  ]
}

# 3. Cuentas de Servicio (SA)
# SA para ms-admin
resource "google_service_account" "ms_admin_sa" {
  account_id   = "ms-admin-sa"
  display_name = "Service Account for ms-admin"
}

# SA para ms-redirect
resource "google_service_account" "ms_redirect_sa" {
  account_id   = "ms-redirect-sa"
  display_name = "Service Account for ms-redirect"
}

# SA para frontend
resource "google_service_account" "frontend_sa" {
  account_id   = "frontend-sa"
  display_name = "Service Account for frontend"
}

# 4. Asignar Permisos (IAM)
# ms-admin y ms-redirect necesitan acceso a Firestore
resource "google_project_iam_member" "firestore_access" {
  for_each = toset([
    google_service_account.ms_admin_sa.email,
    google_service_account.ms_redirect_sa.email
  ])
  project = var.gcp_project_id
  role    = "roles/datastore.user" # Rol para leer/escribir en Firestore
  member  = "serviceAccount:${each.key}"
}

# 5. Desplegar los Servicios de Cloud Run

# ----- ms-admin -----
resource "google_cloud_run_v2_service" "ms_admin" {
  provider = google
  name     = "ms-admin"
  location = var.gcp_region
  
  # --- CAMBIO ---
  # Ahora es PÚBLICO para ser llamado por Axios desde el navegador
  ingress = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.ms_admin_sa.email
    containers {
      image = "docker.io/${var.docker_hub_user}/linkly-ms-admin:latest"
      ports {
        container_port = 8080
      }
      env {
        name  = "PORT"
        value = "8080"
      }
      env {
        name  = "LINKS_COLLECTION"
        value = "links"
      }
      env {
        name  = "METRICS_COLLECTION"
        value = "metrics"
      }
    }
  }
  
  depends_on = [ google_project_service.apis["run.googleapis.com"] ]
}

# ----- ms-redirect -----
resource "google_cloud_run_v2_service" "ms_redirect" {
  provider = google
  name     = "ms-redirect"
  location = var.gcp_region
  
  # Este servicio es PÚBLICO
  ingress = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.ms_redirect_sa.email
    containers {
      image = "docker.io/${var.docker_hub_user}/linkly-ms-redirect:latest"
      ports {
        container_port = 8080
      }
      env {
        name  = "PORT"
        value = "8080"
      }
      env {
        name  = "LINKS_COLLECTION"
        value = "links"
      }
      env {
        name  = "METRICS_COLLECTION"
        value = "metrics"
      }
    }
  }
  depends_on = [ google_project_service.apis["run.googleapis.com"] ]
}

# ----- frontend -----
resource "google_cloud_run_v2_service" "frontend" {
  provider = google
  name     = "frontend"
  location = var.gcp_region
  
  # Este servicio es PÚBLICO
  ingress = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.frontend_sa.email
    containers {
      image = "docker.io/${var.docker_hub_user}/linkly-frontend:latest"
      ports {
        container_port = 5000 # El puerto de Flask
      }
      # Aquí está la magia: inyectamos las URLs de los otros servicios
      # El frontend (JS/Axios) necesita saber la URL del admin
      env {
        name  = "ADMIN_API_URL"
        value = google_cloud_run_v2_service.ms_admin.uri
      }
      env {
        name  = "BASE_DOMAIN"
        value = google_cloud_run_v2_service.ms_redirect.uri
      }
      env {
        name  = "FLASK_PORT"
        value = "5000"
      }
      env {
        name = "FLASK_DEBUG"
        value = "False"
      }
    }
  }
  depends_on = [ google_project_service.apis["run.googleapis.com"] ]
}



# Permitir que CUALQUIERA (allUsers) invoque los servicios públicos
resource "google_cloud_run_service_iam_member" "public_invokers" {
  for_each = toset([
    google_cloud_run_v2_service.frontend.name,
    google_cloud_run_v2_service.ms_redirect.name,
    google_cloud_run_v2_service.ms_admin.name
  ])
  provider = google
  location = var.gcp_region
  project  = var.gcp_project_id
  service  = each.key
  role     = "roles/run.invoker"
  member   = "allUsers"
}

