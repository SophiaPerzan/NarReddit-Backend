from flask import Flask, request, jsonify
from rq import Queue
from redis import Redis
import os
import base64

app = Flask(__name__)
redis_conn = Redis(host='redis')
q = Queue(connection=redis_conn)


@app.before_request
def check_api_key():
    if "Api-Key" not in request.headers or request.headers.get('Api-Key') != os.environ.get('NARREDDIT_API_KEY'):
        return jsonify({"error": "Invalid API key"}), 401


@app.route('/create', methods=['POST'])
def script():
    params = request.form.to_dict()
    if 'IMAGE_FILE' in request.files:
        image = request.files['IMAGE_FILE']
        # Check the content type to determine the file extension
        file_extension = '.jpeg' if image.content_type == 'image/jpeg' else '.png'

        # Create a temporary file with the correct extension
        fileName = f"{params['DOC_ID']}{file_extension}"
        filePath = os.path.join('temp', fileName)
        os.makedirs(os.path.dirname(filePath), exist_ok=True)

        # Save the uploaded image to the temporary file
        image.save(filePath)
        # Convert image to base64
        with open(filePath, 'rb') as image_file:
            encoded_string = base64.b64encode(image_file.read())
        b64Image = encoded_string.decode('utf-8')
        params['IMAGE_FILE'] = b64Image
        params['IMAGE_FILENAME'] = fileName
        os.remove(filePath)
    else:
        params['IMAGE_FILE'] = None
    languages_string = request.form['LANGUAGES']
    numLangs = len(languages_string.split(','))
    timeOut = 600 * numLangs
    job = q.enqueue('worker.script_async', job_timeout=timeOut,
                    args=(params,))
    return jsonify({'status': 'started', 'task_id': job.get_id()}), 202


@app.route('/status', methods=['POST'])
def taskstatus():
    params = request.get_json()
    task_id = params['task_id']
    job = q.fetch_job(task_id)
    if job is None:
        return jsonify({'status': 'unknown'}), 200
    else:
        return jsonify({'status': job.get_status(refresh=True)}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0')
