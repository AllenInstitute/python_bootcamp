# hash:sha256:86587c6d0585a1cde890fa92cc96f8c2d498f6ab0a5652967086fc8dcaa11c33
ARG REGISTRY_HOST
FROM $REGISTRY_HOST/codeocean/code-server-python-extensions-pack:code-server4.129.0python3.12.4codeocean-mcp-serveruvpyreflyetc

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
