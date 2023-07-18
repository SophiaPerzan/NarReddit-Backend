from flask import Flask, request, jsonify, send_file, send_from_directory
from narreddit import NarReddit
import zipfile
import os

app = Flask(__name__)


@app.route('/run', methods=['POST'])
def run():
    params = request.get_json()

    narreddit = NarReddit()
    video_files = narreddit.createVideo(params)

    # create a ZipFile object
    with zipfile.ZipFile('videos.zip', 'w') as zipf:
        # add files to the zip file
        for video in video_files:
            zipf.write(video, arcname=os.path.basename(video))

    return send_file('videos.zip', mimetype='application/zip', as_attachment=True)
