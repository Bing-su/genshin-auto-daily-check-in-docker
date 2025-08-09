variable "TAG" {
    default = "latest"
}

variable "REPOSITORY" {
    default = "ks2515/genshin-auto-daily-check-in"
}

target "default" {
    context = "."
    platforms = ["linux/amd64", "linux/arm64"]
    tags = ["${REPOSITORY}:${TAG}", "${REPOSITORY}:latest"]
}
