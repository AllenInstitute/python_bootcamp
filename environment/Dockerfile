# hash:sha256:df4a060dccdc951cd268723c5ff86c2f901fe45bbbfc86880d4fc94493f6737f
FROM registry.codeocean.allenneuraldynamics.org/codeocean/mambaforge3:22.11.1-4-ubuntu22.04

ARG DEBIAN_FRONTEND=noninteractive

ARG GIT_ASKPASS
ARG GIT_ACCESS_TOKEN
COPY git-askpass /

RUN conda install -y --channel=conda-forge \
        jupyterlab==4.0.5 \
        notebook==7.0.2 \
    && conda clean -ya

RUN pip install -U --no-cache-dir \
    matplotlib==3.7.2 \
    numpy==1.24.0 \
    pandas==2.0.3 \
    pyarrow==12.0.1 \
    scikit-learn==1.3.0 \
    scipy==1.11.1 \
    seaborn==0.12.1 \
    umap-learn==0.5.3

COPY postInstall /
RUN /postInstall
