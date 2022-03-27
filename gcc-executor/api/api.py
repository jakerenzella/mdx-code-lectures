from flask import Flask, request
from flask_cors import CORS, cross_origin

from celery import Celery
import jobs
import json

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379'

app.config.update(
    CELERY_BROKER_URL=app.config['CELERY_BROKER_URL'],
    CELERY_RESULT_BACKEND=app.config['CELERY_RESULT_BACKEND']
)


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


celery = make_celery(app)


@app.route("/register_image", methods=['POST'])
def register():
    body = request.get_json()
    name = body['name']
    jobs.register_image(name)
    return {}


@app.route("/compile", methods=['POST'])
@cross_origin()
def compile_code():
    request_json = json.loads(request.get_data())
    language = request_json.get('language')
    code = request_json.get('code')
    print(language)
    print(code)

    return compile_code_task(code, language)


@celery.task()
def compile_code_task(code, language):
    return jobs.compile(code, language=language)


app.run(port=3000, debug=True, use_debugger=True)
