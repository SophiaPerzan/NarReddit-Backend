from flask import Flask, request, jsonify, send_file, send_from_directory
from rq import Queue
from redis import Redis
import os
from werkzeug.utils import secure_filename

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
        filePath = os.path.join('shared', fileName)

        # Save the uploaded image to the temporary file
        image.save(filePath)

        # Include the temporary file's path in the parameters
        params['IMAGE_FILE'] = filePath
    else:
        params['IMAGE_FILE'] = None
    languages_string = request.form['LANGUAGES']
    numLangs = len(languages_string.split(','))
    timeOut = 300 * numLangs
    job = q.enqueue('worker.script_async', job_timeout=timeOut,
                    args=(params,))
    return jsonify({'status': 'started', 'task_id': job.get_id()}), 202


@app.route('/status', methods=['POST'])
def taskstatus():
    params = request.get_json()
    task_id = params['task_id']
    job = q.fetch_job(task_id)
    if job is None:
        filename = params['DOC_ID']+'.zip'
        if filename is None:
            return jsonify({'error': 'No task with this ID'}), 404
        filepath = os.path.join('shared', filename)
        if not os.path.isfile(filepath):
            return jsonify({'error': 'No task with this ID'}), 404
        else:
            return jsonify({'status': 'finished'}), 200
    else:
        return jsonify({'status': job.get_status(refresh=True)}), 200


@app.route('/download', methods=['POST'])
def download():
    params = request.get_json()
    filename = params['DOC_ID']+'.zip'
    if filename is None:
        return jsonify({'error': 'No filename associated with this task ID'}), 404
    filepath = os.path.join('shared', filename)
    if not os.path.isfile(filepath):
        return jsonify({'error': 'No filepath associated with this task ID'}), 404
    return send_file(path_or_file=filepath, as_attachment=True, download_name=filename)


@app.route('/background', methods=['POST'])
def upload_background():
    params = request.form.to_dict()
    if 'VIDEO_FILE' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    video = request.files['VIDEO_FILE']
    # Check the content type to determine the file extension
    if video.content_type == 'video/mp4':
        file_extension = '.mp4'
    else:
        return jsonify({'error': 'Invalid file type'}), 400
    # Ensure filename is secure
    fileName = secure_filename(video.filename)
    filePath = os.path.join('shared', 'background-videos',
                            params['USER_ID'], fileName)
    # Ensure directory exists
    os.makedirs(os.path.dirname(filePath), exist_ok=True)
    video.save(filePath)
    return jsonify({'status': 'success'}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0')
