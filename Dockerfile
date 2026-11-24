# TeleScope v2 - reproducible environment: Python + Java 17 (for PySpark) + every library of the project.
# The code is NOT copied into the image: docker-compose mounts the project folder on /work,
# so editing a script on the host takes effect immediately and results are written to the host folders.
ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive
# openjdk-17: Spark; procps: Spark launch scripts call `ps`; tini: clean signal handling; make: the Makefile targets
RUN apt-get update \
 && apt-get install -y --no-install-recommends openjdk-17-jre-headless procps tini make \
 && rm -rf /var/lib/apt/lists/* \
 && ln -s "$(dirname "$(dirname "$(readlink -f "$(which java)")")")" /opt/java
ENV JAVA_HOME=/opt/java

# same user id as the host user, so the files written in the mounted folders belong to you, not to root
ARG UID=1000
ARG GID=1000
RUN groupadd -g "${GID}" telescope && useradd -m -u "${UID}" -g "${GID}" -s /bin/bash telescope \
 && mkdir -p /spark_tmp /work && chown telescope:telescope /spark_tmp /work

WORKDIR /work
# requirements.lock (exact versions) is used when it exists, otherwise requirements.txt
COPY requirements.tx[t] requirements.loc[k] /tmp/req/
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r "$(test -f /tmp/req/requirements.lock && echo /tmp/req/requirements.lock || echo /tmp/req/requirements.txt)" \
 && pip freeze > /etc/pip-freeze.txt

# Spark settings read by bigdata_pipeline/spark/spark_session.py (3 cores, 4 GB for the JVM, shuffle files in /spark_tmp)
ENV TELESCOPE_CORES=3 \
    TELESCOPE_SPARK_MEMORY=4g \
    TELESCOPE_SPARK_TMP=/spark_tmp \
    TELESCOPE_SHUFFLE_PARTITIONS=48 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=0 \
    MPLBACKEND=Agg \
    TZ=UTC \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8

USER telescope
ENTRYPOINT ["tini", "--"]
CMD ["bash"]