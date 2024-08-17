# hash:sha256:efca1172edd3536abcab9d002ad19a753489bd210364d571fb733a92fb2bc5a2
ARG REGISTRY_HOST
FROM $REGISTRY_HOST/codeocean/mambaforge3:23.1.0-4-python3.10.12-ubuntu22.04

ARG DEBIAN_FRONTEND=noninteractive

ARG GIT_ASKPASS
ARG GIT_ACCESS_TOKEN
COPY git-askpass /

RUN mamba install -y \
        jupyterlab==3.6.2 \
        matplotlib==3.7.2 \
        notebook==6.5.4 \
        numpy==1.24.4 \
        pandas==2.0.3 \
        scikit-learn==1.3.0 \
        scipy==1.11.1 \
        seaborn==0.12.2 \
    && mamba clean -ya

RUN pip install -U --no-cache-dir \
    pyarrow==12.0.1 \
    umap-learn==0.5.3

COPY postInstall /
RUN /postInstall
