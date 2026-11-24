"""TeleScope v2: the whole project as one Airflow DAG (no schedule: triggered by hand, or set `schedule`).
Each task runs `make RUN= <target>` inside the telescope:v2 image, so the commands live only in the Makefile.
Order = the step numbers of the scripts: theme 1-3, then theme 4 (th4-1..th4-5 with job5 between 3 and 4), then job6 and theme 5 (th5-1..th5-5).
The pool "spark" has one slot: two Spark jobs never run together (8 GB of RAM).
"""
import os
from datetime import datetime

from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount

PROJECT = os.environ["PROJECT_DIR"]          # absolute host paths: Docker mounts them from the host
RAW = os.path.abspath(os.path.join(PROJECT, os.environ.get("RAW_DIR", "telescope_raw")))
TMP = os.path.abspath(os.path.join(PROJECT, os.environ.get("SPARK_TMP", "spark_tmp")))
IMAGE = "telescope:v2"
USER = f"{os.environ.get('HOST_UID', '1000')}:{os.environ.get('HOST_GID', '1000')}"

# 0 = no limit for the pool is not allowed; create the pool once: airflow pools set spark 1 "one Spark job at a time"
POOL = "spark"


def step(dag, target):
    return DockerOperator(
        task_id=target,
        image=IMAGE,
        command=f"make RUN= {target}",
        working_dir="/work",
        user=USER,
        auto_remove="success",
        docker_url="unix://var/run/docker.sock",
        mount_tmp_dir=False,
        mounts=[Mount("/work", PROJECT, type="bind"),
                Mount("/raw", RAW, type="bind", read_only=True),
                Mount("/spark_tmp", TMP, type="bind")],
        environment={k: os.environ[k] for k in ("TELESCOPE_CORES", "TELESCOPE_SPARK_MEMORY") if k in os.environ},
        pool=POOL,
        dag=dag,
    )


with DAG("telescope_full", start_date=datetime(2026, 1, 1), schedule=None, catchup=False, max_active_runs=1,
         tags=["telescope"]) as dag:
    def chain(*names):
        """Tasks that must run one after the other."""
        tasks = [t[n] if n in t else t.setdefault(n, step(dag, n)) for n in names]
        for x, y in zip(tasks, tasks[1:]):
            x >> y
        return tasks

    t = {}
    chain("pipeline", "theme1", "theme2", "theme3")
    chain("pipeline", "th4-1", "th4-2", "th4-3", "job5", "th4-4", "th4-5")
    chain("pipeline", "job6", "th5-1", "th5-2", "th5-3", "th5-4", "th5-5")
    # the three branches are put one after the other: a single Spark / analysis job at a time (8 GB RAM);
    # theme 5 (review list) reads the cities written by th4-2
    t["theme3"] >> t["th4-1"]
    t["th4-5"] >> t["job6"]