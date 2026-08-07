FROM ghcr.io/denoland/deno:bin-2.9.5 as deno

FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim

WORKDIR /app

# immediately print stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    UV_NO_CACHE=1 \
    UV_SYSTEM_PYTHON=1 \
    UV_NO_DEV=1 \
    UV_COMPILE_BYTECODE=1 \
    # put pip packages on PATH
    PATH=/app/.local/bin:${PATH}

RUN export DEBIAN_FRONTEND=noninteractive \
    && set -ex \
    # add python group & user
    && groupadd --gid 999 python \
    && useradd --uid 999 --gid 999 --home /app python \
    # ensure /app is owned by the python user
    && chown python:python /app \
    # install ffmpeg
    && apt update \
    && apt install ffmpeg --no-install-recommends --no-install-suggests -y \
    # update other packages and clean up
    && apt upgrade -y \
    && apt clean -y \
    && rm -rf /var/lib/apt/lists/*

# copy deno to PATH for yt-dlp EJS
COPY --from=deno /deno /usr/local/bin/deno

ARG PACKAGE_VERSION
RUN uv pip install vidfetch_bot==${PACKAGE_VERSION}

USER python

CMD [ "python3", "-m", "vidfetch_bot" ]