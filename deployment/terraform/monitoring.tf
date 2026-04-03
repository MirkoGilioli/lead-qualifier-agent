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

# 1. Definizione della Log-based Metric (Distribuzione della Latenza)
resource "google_logging_metric" "agent_run_latency_metric" {
  name    = "agent_run_latency_${var.env}"
  project = var.project_id
  filter  = "jsonPayload.event=\"sre_metric\" AND jsonPayload.metric_name=\"agent_run_duration_ms\""

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "DISTRIBUTION"
    unit        = "ms"
    display_name = "Agent Run Latency (JSON-based) - ${var.env}"
  }

  # Estrae direttamente il valore dal campo JSON 'value'
  value_extractor = "EXTRACT(jsonPayload.value)"

  bucket_options {
    exponential_buckets {
      num_finite_buckets = 64
      growth_factor      = 2
      scale              = 1
    }
  }
}

# 2. Definizione del Servizio Monitorato
resource "google_monitoring_custom_service" "agent_service" {
  service_id   = "${var.project_name}-agent-${var.env}"
  display_name = "Agent ADK Service (${var.env})"
  project      = var.project_id
}

# 3. SLO di Latenza basato sulla metrica log-based
resource "google_monitoring_slo" "latency_slo" {
  service      = google_monitoring_custom_service.agent_service.service_id
  slo_id       = "latency-agent-run"
  display_name = "Latenza agent_run < ${var.slo_latency_threshold_ms}ms"
  project      = var.project_id

  goal                = var.slo_target_percent
  rolling_period_days = 30

  request_based_sli {
    distribution_cut {
      # Puntiamo alla metrica log-based appena creata
      distribution_filter = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.agent_run_latency_metric.name}\" resource.type=\"global\""
      range {
        max = var.slo_latency_threshold_ms
      }
    }
  }
}

# 4. Alert Policy
resource "google_monitoring_alert_policy" "slo_burn_rate_alert" {
  display_name = "SLO Burn Rate Alert: agent_run Latency (${var.env})"
  project      = var.project_id
  combiner     = "OR"
  conditions {
    display_name = "Burn rate too high"
    condition_threshold {
      filter     = "select_slo_burn_rate(\"projects/${var.project_id}/services/${google_monitoring_custom_service.agent_service.service_id}/serviceLevelObjectives/${google_monitoring_slo.latency_slo.slo_id}\", \"1h\")"
      duration   = "0s"
      comparison = "COMPARISON_GT"
      threshold_value = 1.0
      trigger {
        count = 1
      }
    }
  }
  notification_channels = []
}
