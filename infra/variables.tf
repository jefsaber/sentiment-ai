variable "image_tag" {
  description = "Tag de l'image Docker à déployer"
  type        = string
  default     = "latest"
}

variable "app_port" {
  description = "Port exposé en staging"
  type        = number
  default     = 8001
}

variable "container_name" {
  description = "Nom du conteneur staging"
  type        = string
  default     = "sentiment-staging"
}

variable "registry" {
  description = "Registry Docker"
  type        = string
  default     = "ghcr.io/jefsaber"
}

variable "docker_host" {
  description = "Docker host used by Terraform"
  type        = string
  default     = "npipe:////./pipe/docker_engine"
}