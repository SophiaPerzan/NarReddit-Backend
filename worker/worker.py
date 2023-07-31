from redis import Redis
from rq import Worker, Queue
import zipfile
import os
from narreddit import NarReddit

print("Running code")
listen = ['default']
conn = Redis(host="redis", port=6379)
worker = Worker(map(Queue, listen), connection=conn)

if __name__ == '__main__':
    worker.work()


def script_async(params):
    narreddit = NarReddit()
    video_files = narreddit.createVideo(params)

    # create a ZipFile object
    zip_filename = os.path.join('shared', params['DOC_ID']+'.zip')
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        # add files to the zip file
        for video in video_files:
            zipf.write(video, arcname=os.path.basename(video))
            os.remove(video)
    print("Created zip file")
