import docker
import os
from pathlib import Path
import uuid
import shutil

import logging

logger = logging.getLogger("gcc-executor")

TEMP_PATH = Path(__file__).resolve().parents[1] / 'temp'

client = docker.from_env()


def get_temp_dir(job_id):
    return f"{TEMP_PATH}/{job_id}"


def create_temp_codefile(code, job_id):
    filename = f"{get_temp_dir(job_id)}/program.c"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w+") as f:
        f.write(code)


def register_image(image):
    client.images.pull(image)


def cleanup(job_id):
    print("cleaning files")
    shutil.rmtree(get_temp_dir(job_id), ignore_errors=True)


def get_output(job_id):
    print(f"getting output for {job_id}")
    filename = f"{get_temp_dir(job_id)}/output.txt"
    with open(filename, "r") as f:
        output = f.read()
    print(f"output: {output}")
    return output


def compile(code, image="gcc:latest", language="c"):
    job_id = uuid.uuid4()
    create_temp_codefile(code, job_id)
    print(f"compiling {job_id}")
    container = client.containers.run(image,
                                      '/bin/bash -c "gcc -o /code/program /code/program.c && /code/program > /code/output.txt"',
                                      volumes={get_temp_dir(job_id): {
                                          'bind': '/code', 'mode': 'rw'}},
                                      working_dir='/code',
                                      detach=True)
    print(f"Waiting for container")
    result = container.wait()

    print(f"Getting output")
    output = get_output(job_id)

    print(f"Removing container")
    container.remove()
    print(f"Cleaning container")
    cleanup(job_id)

    print(f"returning {output}")
    return output
