# hash:sha256:9a8ef6d84011d9c3318a1801bf15b49b0f70be447692b3d40a15b776c5265a3f
ARG REGISTRY_HOST
FROM $REGISTRY_HOST/codeocean/swdb:Python3.12code-server4.133

ARG DEBIAN_FRONTEND=noninteractive
ARG GIT_ASKPASS
COPY git-ask-pass /

RUN mamba install -y \
        jupyterlab==4.6.3 \
        libxml2==2.12.7 \
        matplotlib==3.10.9 \
        notebook==7.6.2 \
        numpy==2.5.2 \
        pandas==3.0.5 \
        scikit-learn==1.9.0 \
        scipy==1.18.0 \
        seaborn==0.13.2 \
    && mamba clean -ya

RUN pip install -U --no-cache-dir \
    pyarrow==25.0.1 \
    umap-learn==0.5.12

COPY postInstall /
RUN --mount=type=secret,id=secrets . /run/secrets/secrets \
    && /postInstall
