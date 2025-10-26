output "frontend_url" {
  description = "URL del servicio de Frontend"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "redirect_url" {
  description = "URL del servicio de Redirección (ms-redirect)"
  value       = google_cloud_run_v2_service.ms_redirect.uri
}

output "admin_api_url" {
  description = "URL interna del servicio de Admin (ms-admin)"
  value       = google_cloud_run_v2_service.ms_admin.uri
}