# hash:sha256:62dea985b8ed751368fd878dfad266d8710fe137c85dbcc4dd38fc7f1518dda7
FROM registry.codeocean.allenneuraldynamics.org/codeocean/mambaforge3:22.11.1-4-ubuntu22.04

ARG DEBIAN_FRONTEND=noninteractive

ARG GIT_ASKPASS
ARG GIT_ACCESS_TOKEN
COPY git-askpass /

RUN conda install -y \
        jupyterlab==4.0.4 \
        notebook==7.0.2 \
    && conda clean -ya
