from redis import Redis
from rq import Worker, Queue
import zipfile
import os
from narreddit import NarReddit
from google.cloud import storage
import base64

print("Running code")
storage_client = storage.Client()
bucket = storage_client.bucket("narreddit-nr.appspot.com")
listen = ['default']
conn = Redis(host="redis", port=6379)
worker = Worker(map(Queue, listen), connection=conn)

if __name__ == '__main__':
    worker.work()


def script_async(params):

    params['SUBTITLES'] = params['SUBTITLES'].lower() == 'true'
    params['RANDOM_START_TIME'] = params['RANDOM_START_TIME'].lower() == 'true'

    if params.get('IMAGE_FILE') is not None:
        filePath = os.path.join('temp', params['IMAGE_FILENAME'])
        os.makedirs(os.path.dirname(filePath), exist_ok=True)

        # Convert the b64 image back to an image
        convert_base64_to_image(params['IMAGE_FILE'], filePath)
        params['IMAGE_FILE'] = filePath
    try:
        narreddit = NarReddit(bucket)
        video_files = narreddit.createVideo(params)

        # create a ZipFile object
        zip_filename = os.path.join('temp', params['DOC_ID']+'.zip')
        os.makedirs(os.path.dirname(zip_filename), exist_ok=True)
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            # add files to the zip file
            for video in video_files:
                zipf.write(video, arcname=os.path.basename(video))
                os.remove(video)
        print("Created zip file")
        destination_blob_name = params['USER_ID'] + \
            '/videos/'+params['DOC_ID']+'.zip'
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(zip_filename)
        print(f"File {zip_filename} uploaded to {destination_blob_name}.")
        os.remove(zip_filename)
    except Exception as e:
        raise Exception(e)


def convert_base64_to_image(base64_string, output_path):
    image_data = base64.b64decode(base64_string)
    with open(output_path, 'wb') as f:
        f.write(image_data)
