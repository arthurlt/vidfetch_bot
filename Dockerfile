FROM python:3.11-slim-bookworm

WORKDIR /app

# immediately print stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    # disable the pip version warning
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # useless in container
    PIP_NO_CACHE_DIR=1

ARG PACKAGE_VERSION
RUN set -ex &&\
    # add python group & user
    groupadd --gid 1000 python &&\
    useradd --uid 1000 --gid 1000 --home /app python &&\
    # ensure /app is owned by the python user
    chown python:python /app &&\
    # update the packages and clean up
    apt update &&\
    apt upgrade -y &&\
    apt clean -y &&\
    rm -rf /var/lib/apt/lists/*

USER python

RUN pip install vidfetch_bot==${PACKAGE_VERSION}

CMD [ "python3", "-m", "vidfetch_bot" ]