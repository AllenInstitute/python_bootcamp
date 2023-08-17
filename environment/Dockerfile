# hash:sha256:04c2b60c1845efd47fe4dab66e7a78dc9acf25e76359ad16486d52dabdb36c6b
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
    scikit-learn==1.3.0 \
    scipy==1.11.1 \
    seaborn==0.12.1 \
    umap-learn==0.5.3

COPY postInstall /
RUN /postInstall
