from pathlib import Path
import shutil
import uuid
import os

import logging
import docker

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
    try:
        with open(filename, "r") as f:
            output = f.read()
        print(f"output: {output}")
    except FileNotFoundError:
        raise FileNotFoundError("No output file found, could not compile")
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
    print("Waiting for container")
    try:
        result = container.wait(timeout=60)
    except Exception:
        return {'output': None, 'status_code': -1, 'error': 'Compilation timed out'}

    print("Getting output")
    try:
        output = {'output': get_output(
            job_id), 'status_code': result['StatusCode'], 'error': result['Error']}
    except FileNotFoundError as exception:
        output = {'output': None,
                  'status_code': result['StatusCode'], 'error': str(exception)}

    print("Removing container")
    container.remove()
    print("Cleaning container")
    cleanup(job_id)

    print(f"returning {output}")
    return output
