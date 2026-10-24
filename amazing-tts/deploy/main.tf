terraform {

  required_version = ">= 1.6"
  required_providers {

    google = {
      source  = "hashicorp/google",
      version = "~> 6.0"
    }

  }

}

variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "image" {
  type = string
}

variable "bucket_name" {
  type = string
}

variable "gemini_model" {
  type = string
}

variable "firebase_api_key" {
  type = string
}

variable "firebase_auth_domain" {
  type = string
}

variable "daily_budget" {
  type    = string
  default = "480"
}

variable "edition" {
  type    = string
  default = "v1"
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_project_service" "apis" {

  for_each           = toset(["run.googleapis.com", "cloudtasks.googleapis.com", "firestore.googleapis.com", "storage.googleapis.com", "secretmanager.googleapis.com", "iamcredentials.googleapis.com", "identitytoolkit.googleapis.com"])
  service            = each.value
  disable_on_destroy = false

}

resource "google_service_account" "api" {
  account_id = "amazing-tts-api"
}

resource "google_service_account" "worker" {
  account_id = "amazing-tts-worker"
}

resource "google_service_account" "tasks" {
  account_id = "amazing-tts-tasks"
}

resource "google_storage_bucket" "audio" {

  name                        = var.bucket_name
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false
  versioning {
    enabled = true
  }

  lifecycle {
    prevent_destroy = true
  }

}

resource "google_firestore_database" "library" {

  name                    = "(default)"
  location_id             = var.region
  type                    = "FIRESTORE_NATIVE"
  delete_protection_state = "DELETE_PROTECTION_ENABLED"
  depends_on              = [google_project_service.apis]
  lifecycle {
    prevent_destroy = true
  }

}

resource "google_secret_manager_secret" "gemini" {

  secret_id = "amazing-tts-gemini-key"
  replication {
    auto {

    }

  }

  depends_on = [google_project_service.apis]

}

# Deliberately no secret version in Terraform state. Add it with gcloud before deploying the worker.
resource "google_cloud_tasks_queue" "chapters" {

  name     = "amazing-tts"
  location = var.region
  rate_limits {
    max_concurrent_dispatches = 1
    max_dispatches_per_second = 0.1
  }

  retry_config {
    max_attempts       = 20
    min_backoff        = "30s"
    max_backoff        = "3600s"
    max_retry_duration = "86400s"
  }

  depends_on = [google_project_service.apis]

}

locals {

  shared_env = {

    AMAZING_TTS_CLOUD    = "1"
    AUDIO_BUCKET         = var.bucket_name
    GOOGLE_CLOUD_PROJECT = var.project_id
    CLOUD_REGION         = var.region
    TASK_QUEUE           = google_cloud_tasks_queue.chapters.name
    TASK_SERVICE_ACCOUNT = google_service_account.tasks.email
    GEMINI_MODEL         = var.gemini_model
    GEMINI_DAILY_BUDGET  = var.daily_budget
    GEMINI_RPM           = "5"
    GEMINI_TPM           = "100000"
    AUDIOBOOK_EDITION    = var.edition

  }

}

resource "google_project_iam_member" "datastore" {

  for_each = {
    api = google_service_account.api.email, worker = google_service_account.worker.email
  }

  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${each.value}"

}

resource "google_project_iam_member" "enqueuer" {

  for_each = {
    api = google_service_account.api.email, worker = google_service_account.worker.email
  }

  project = var.project_id
  role    = "roles/cloudtasks.enqueuer"
  member  = "serviceAccount:${each.value}"

}

resource "google_service_account_iam_member" "act_as_task" {

  for_each = {
    api = google_service_account.api.email, worker = google_service_account.worker.email
  }

  service_account_id = google_service_account.tasks.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${each.value}"

}

resource "google_storage_bucket_iam_member" "objects" {

  for_each = {
    api = google_service_account.api.email, worker = google_service_account.worker.email
  }

  bucket = google_storage_bucket.audio.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${each.value}"

}

resource "google_secret_manager_secret_iam_member" "worker_key" {

  secret_id = google_secret_manager_secret.gemini.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.worker.email}"

}

resource "google_service_account_iam_member" "sign" {

  service_account_id = google_service_account.api.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:${google_service_account.api.email}"

}

resource "google_project_iam_member" "firebase" {

  project = var.project_id
  role    = "roles/firebaseauth.viewer"
  member  = "serviceAccount:${google_service_account.api.email}"

}

resource "google_cloud_run_v2_service" "worker" {

  name                = "amazing-tts-worker"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false
  template {

    service_account                  = google_service_account.worker.email
    timeout                          = "1800s"
    max_instance_request_concurrency = 1
    scaling {
      min_instance_count = 0
      max_instance_count = 1
    }

    containers {

      image = var.image
      resources {
        limits = {
          cpu = "2", memory = "4Gi"
        }

        cpu_idle          = true
        startup_cpu_boost = true
      }

      dynamic "env" {
        for_each = merge(local.shared_env, {
          SERVICE_MODE = "worker", OMP_NUM_THREADS = "2", MKL_NUM_THREADS = "2"
          }
        )
        content {
          name  = env.key
          value = env.value
        }

      }

      env {
        name = "GEMINI_API_KEY"
        value_source {

          secret_key_ref {
            secret  = google_secret_manager_secret.gemini.secret_id
            version = "latest"
          }

        }

      }

      startup_probe {
        http_get {
          path = "/health"
          port = 8080
        }

        initial_delay_seconds = 5
        period_seconds        = 10
        failure_threshold     = 24
      }

    }

  }

  depends_on = [google_project_service.apis, google_secret_manager_secret_iam_member.worker_key]

}

resource "google_cloud_run_v2_service_iam_member" "private_worker" {

  location = var.region
  name     = google_cloud_run_v2_service.worker.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.tasks.email}"

}

resource "google_cloud_run_v2_service" "api" {

  name                = "amazing-tts"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false
  template {

    service_account = google_service_account.api.email
    timeout         = "120s"
    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }

    containers {

      image = var.image
      resources {
        limits = {
          cpu = "1", memory = "512Mi"
        }

        cpu_idle = true
      }

      dynamic "env" {

        for_each = merge(local.shared_env, {
          SERVICE_MODE = "api", WORKER_URL = google_cloud_run_v2_service.worker.uri, SIGNING_SERVICE_ACCOUNT = google_service_account.api.email, FIREBASE_API_KEY = var.firebase_api_key, FIREBASE_AUTH_DOMAIN = var.firebase_auth_domain
          }
        )

        content {
          name  = env.key
          value = env.value
        }

      }

    }

  }

  depends_on = [google_project_service.apis]

}

resource "google_cloud_run_v2_service_iam_member" "public_api" {

  location = var.region
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"

}

output "website_url" {

  value = google_cloud_run_v2_service.api.uri
}

output "bucket" {

  value = google_storage_bucket.audio.name
}

