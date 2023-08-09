import ffmpeg
import os
import random


class VideoGenerator:
    def __init__(self, env):
        self.env = env

    def generateVideo(self, ttsAudioPath, outputVideoPath, directory, subtitlesPath, params):
        backgroundVideoPath = self.getBackgroundVideoPath(
            params['BG_VIDEO_FILENAME'], directory)

        if not os.path.isfile(backgroundVideoPath):
            print(f"Video file not found: {backgroundVideoPath}")
            return False

        if not os.path.isfile(ttsAudioPath):
            print(f"Audio file not found: {ttsAudioPath}")
            return False

        audioDuration = self.getAudioDuration(ttsAudioPath)
        videoProbe = ffmpeg.probe(backgroundVideoPath)
        videoStream = self.getVideoStream(videoProbe)
        videoDuration = float(videoStream['duration'])

        startTime = self.getStartTime(
            audioDuration, videoDuration, params['RANDOM_START_TIME'])

        # Calculate new dimensions only when necessary
        newWidth, newHeight = None, None
        if videoStream['width'] != 9 or videoStream['height'] != 16:
            newWidth, newHeight = self.getNewDimensions(videoStream)

        imageFile = None
        image_stream = None
        if params['IMAGE_FILE'] is not None:
            if not os.path.isfile(params['IMAGE_FILE']):
                print(f"Image file not found: {params['IMAGE_FILE']}")
                return False
            imageFile = params['IMAGE_FILE']
            image_stream = self.processImage(imageFile, newWidth)

        video = self.processVideo(
            backgroundVideoPath, videoDuration, audioDuration, startTime, newWidth, newHeight, subtitlesPath, image_stream=image_stream)
        audio = ffmpeg.input(ttsAudioPath)

        self.mergeAudioVideo(video, audio, outputVideoPath)

        return outputVideoPath

    def getBackgroundVideoPath(self, backgroundVideoFileName, directory):
        if backgroundVideoFileName.upper() == 'RANDOM':
            return self.getRandomMP4(directory)
        else:
            return os.path.join(directory, backgroundVideoFileName)

    def getAudioDuration(self, ttsAudioPath):
        probe = ffmpeg.probe(ttsAudioPath)
        return float(probe['streams'][0]['duration'])+2

    def getVideoStream(self, videoProbe):
        return next((stream for stream in videoProbe['streams'] if stream['codec_type'] == 'video'), None)

    def getStartTime(self, audioDuration, videoDuration, randomizeStart):
        if videoDuration > audioDuration and randomizeStart:
            return random.uniform(0, videoDuration - audioDuration)
        else:
            return 0

    def getNewDimensions(self, videoStream):
        width = int(videoStream['width'])
        height = int(videoStream['height'])

        if width / height > 9 / 16:  # wider than 9:16, crop sides
            return int(height * (9 / 16)), height
        else:  # narrower than 9:16, crop top and bottom
            return width, int(width * (16 / 9))

    def processVideo(self, backgroundVideoPath, videoDuration, audioDuration, startTime, newWidth, newHeight, subtitlesPath, image_stream=None):
        video = ffmpeg.input(backgroundVideoPath)

        # Loop the video if it is shorter than the audio
        if videoDuration < audioDuration:
            loopsNeeded = int(audioDuration // videoDuration) + 1
            videos = [video for _ in range(loopsNeeded)]
            video = ffmpeg.concat(*videos, v=1, a=0)

        # Trim the video to match the length of the audio and crop to the desired aspect ratio
        video = video.trim(start=startTime, end=startTime + audioDuration)
        video = video.setpts('PTS-STARTPTS')

        # Crop the video to the desired aspect ratio if dimensions were calculated
        if newWidth is not None and newHeight is not None:
            video = ffmpeg.filter_(video, 'crop', newWidth, newHeight)

        # Scale the video to 1080x1920 max resolution
        video = ffmpeg.filter_(video, 'scale', 'min(1080,iw)', '-1')

        # Overlay the image if provided
        if image_stream is not None:
            video = ffmpeg.overlay(
                video, image_stream, x='(W-w)/2', y='(H-h)/2', enable='between(t,0,5)')

        # Add subtitles if provided
        if subtitlesPath is not None and os.path.isfile(subtitlesPath):
            # Set style for the subtitles
            style = "FontName=Londrina Solid,FontSize=20,PrimaryColour=&H00ffffff,OutlineColour=&H00000000," \
                    "BackColour=&H80000000,Bold=1,Italic=0,Alignment=10"
            video = ffmpeg.filter_(
                video, 'subtitles', subtitlesPath, force_style=style)

        return video

    def processImage(self, imageFile, videoNewWidth):
        # If an image file is provided, overlay it for the first 5 seconds
        if imageFile is not None:
            image_stream = ffmpeg.input(imageFile)

            videoWidth = min(1080, videoNewWidth)
            imageWidth = min(864, int(videoWidth*0.8))

            # Scale the image to match the video's dimensions if needed
            image_stream = image_stream.filter_('scale', imageWidth, -1)
            return image_stream

    def mergeAudioVideo(self, video, audio, outputVideoPath):
        vcodec = self.env['VCODEC']
        numThreads = self.env['THREADS']
        output = ffmpeg.output(video, audio, outputVideoPath,
                               vcodec=vcodec, threads=numThreads)
        output = ffmpeg.overwrite_output(output)
        ffmpeg.run(output)

    def getRandomMP4(self, directory):
        # Filter the list to include only .mp4 files
        mp4Files = [entry.path for entry in os.scandir(
            directory) if entry.is_file() and entry.name.endswith('.mp4')]

        # Select a random .mp4 file
        randomMP4 = random.choice(mp4Files)

        return randomMP4
