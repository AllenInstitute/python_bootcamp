# hash:sha256:a6670205c4bbb77c149ae554a4de0dab3bf9e341416e81b4a85f34a694c89a1a
ARG REGISTRY_HOST
FROM $REGISTRY_HOST/codeocean/code-server-python-extensions-pack:code-server4.129.0python3.12.4codeocean-mcp-serveruvpyreflyetc

ARG DEBIAN_FRONTEND=noninteractive
ARG GIT_ASKPASS
COPY git-ask-pass /

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
RUN --mount=type=secret,id=secrets . /run/secrets/secrets \
    && /postInstall
