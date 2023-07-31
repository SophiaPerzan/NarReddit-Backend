from flask import Flask, request, jsonify, send_file, send_from_directory
from rq import Queue
from redis import Redis
import os

app = Flask(__name__)
redis_conn = Redis(host='redis')
q = Queue(connection=redis_conn)
cache = {}
id_to_file = {}


@app.before_request
def check_api_key():
    if "Api-Key" not in request.headers or request.headers.get('Api-Key') != os.environ.get('NARREDDIT_API_KEY'):
        return jsonify({"error": "Invalid API key"}), 401


@app.route('/create', methods=['POST'])
def script():
    params = request.get_json()
    hashedParams = hash(frozenset(params.items()))
    print("Hashed params: "+str(hashedParams))
    job = q.enqueue('worker.script_async', params, hashedParams)
    cache[hashedParams] = job.get_id()
    id_to_file[job.get_id()] = hashedParams
    return jsonify({'status': 'started', 'task_id': job.get_id()}), 202


@app.route('/status', methods=['GET'])
def taskstatus():
    params = request.get_json()
    task_id = params['task_id']
    job = q.fetch_job(task_id)
    if job is None:
        return jsonify({'error': 'No task with this ID'}), 404
    return jsonify({'status': job.get_status(refresh=True)}), 200


@app.route('/download', methods=['GET'])
def download():
    params = request.get_json()
    filename = str(id_to_file.get(task_id))+'.zip'
    if filename is None:
        return jsonify({'error': 'No filename associated with this task ID'}), 404
    filepath = os.path.join('shared', filename)
    if not os.path.isfile(filepath):
        return jsonify({'error': 'No filepath associated with this task ID'}), 404
    return send_file(path_or_file=filepath, as_attachment=True, download_name=filename)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
