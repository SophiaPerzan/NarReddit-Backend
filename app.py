from flask import Flask, request, jsonify, send_file, send_from_directory
from narreddit import NarReddit
import zipfile
import os

app = Flask(__name__)


@app.route('/script', methods=['POST'])
def script():
    params = request.get_json()
    print("received request")

    narreddit = NarReddit()
    video_files = narreddit.createVideo(params)

    # create a ZipFile object
    with zipfile.ZipFile('videos.zip', 'w') as zipf:
        # add files to the zip file
        for video in video_files:
            zipf.write(video, arcname=os.path.basename(video))
    print("created zip file")
    return send_file('videos.zip', mimetype='application/zip', as_attachment=True)


if __name__ == '__main__':
    app.run()
