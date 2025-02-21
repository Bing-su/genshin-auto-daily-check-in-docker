variable "tag" {
    default = "1.7.4"
}

variable "repository" {
    default = "ks2515/genshin-auto-daily-check-in"
}

target "default" {
    context = "."
    platforms = ["linux/amd64", "linux/arm64"]
    tags = ["${repository}:latest", "${repository}:${tag}"]
}
