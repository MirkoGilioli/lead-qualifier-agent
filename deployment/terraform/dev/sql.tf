# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

resource "random_id" "db_name_suffix" {
  byte_length = 4
}

resource "random_password" "session_db_password" {
  length           = 16
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "google_secret_manager_secret" "db_password_secret" {
  secret_id = "${var.project_name}-db-password"
  project   = var.project_id
  replication {
    auto {}
  }
  depends_on = [google_project_service.services]
}

resource "google_secret_manager_secret_version" "db_password_version" {
  secret      = google_secret_manager_secret.db_password_secret.id
  secret_data = random_password.session_db_password.result
}

# ------------------------------------------------------------------------------
# Private Service Access configuration for Cloud SQL
# ------------------------------------------------------------------------------
resource "google_project_service" "servicenetworking" {
  project            = var.project_id
  service            = "servicenetworking.googleapis.com"
  disable_on_destroy = false
  depends_on         = [google_project_service.services]
}

resource "google_compute_global_address" "private_ip_address" {
  name          = "private-ip-address"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = "projects/${var.project_id}/global/networks/default"
  project       = var.project_id
  depends_on    = [google_project_service.servicenetworking]
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = "projects/${var.project_id}/global/networks/default"
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
  depends_on              = [google_project_service.servicenetworking]
}
# ------------------------------------------------------------------------------

resource "google_sql_database_instance" "session_db_instance" {
  name             = "${var.project_name}-session-db-${random_id.db_name_suffix.hex}"
  project          = var.project_id
  region           = var.region
  database_version = "POSTGRES_15"

  settings {
    tier = "db-f1-micro"
    
    backup_configuration {
      enabled = true
    }

    ip_configuration {
      ipv4_enabled                                  = false
      private_network                               = "projects/${var.project_id}/global/networks/default"
      enable_private_path_for_google_cloud_services = true
    }
  }

  deletion_protection = false # Set to true for production
  depends_on          = [google_project_service.services, google_service_networking_connection.private_vpc_connection]
}

resource "google_sql_database" "session_db" {
  name     = "sessions"
  instance = google_sql_database_instance.session_db_instance.name
  project  = var.project_id
}

resource "google_sql_user" "session_db_user" {
  name     = "adk_user"
  instance = google_sql_database_instance.session_db_instance.name
  password = random_password.session_db_password.result
  project  = var.project_id
}

output "cloud_sql_connection_name" {
  value = google_sql_database_instance.session_db_instance.connection_name
}
