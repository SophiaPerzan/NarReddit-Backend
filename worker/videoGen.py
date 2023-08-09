import ffmpeg
import os
import random
import tempfile


class VideoGenerator:
    def __init__(self, env):
        self.env = env

    def generateVideo(self, titleAudioPath, descriptionAudioPath, outputVideoPath, backgroundVideoPath, titleSubtitlesPath, descriptionSubtitlesPath, params):
        if not os.path.isfile(backgroundVideoPath):
            print(f"Video file not found: {backgroundVideoPath}")
            return False

        if not os.path.isfile(titleAudioPath):
            print(f"Audio file not found: {titleAudioPath}")
            return False

        if not os.path.isfile(descriptionAudioPath):
            print(f"Audio file not found: {descriptionAudioPath}")
            return False

        hasImage = False
        if params['IMAGE_FILE'] is not None:
            if not os.path.isfile(params['IMAGE_FILE']):
                print(f"Image file not found: {params['IMAGE_FILE']}")
                return False
            else:
                hasImage = True

        titleAudioDuration = self.getAudioDuration(
            titleAudioPath)
        descriptionAudioDuration = self.getAudioDuration(descriptionAudioPath)
        mergedAudio = self.mergeAudio(titleAudioPath, descriptionAudioPath)
        mergedSubtitlesPath = self.mergeSubtitles(
            titleSubtitlesPath, descriptionSubtitlesPath, titleAudioDuration, hasImage)
        # Subtitles are in a temp file

        mergedAudioDuration = titleAudioDuration + descriptionAudioDuration + 2
        videoProbe = ffmpeg.probe(backgroundVideoPath)
        videoStream = self.getVideoStream(videoProbe)
        videoDuration = float(videoStream['duration'])

        startTime = self.getStartTime(
            mergedAudioDuration, videoDuration, params['RANDOM_START_TIME'])

        # Calculate new dimensions only when necessary
        newWidth, newHeight = None, None
        if videoStream['width'] != 9 or videoStream['height'] != 16:
            newWidth, newHeight = self.getNewDimensions(videoStream)

        imageFile = None
        image_stream = None
        if hasImage:
            imageFile = params['IMAGE_FILE']
            image_stream = self.processImage(imageFile, newWidth)

        video = self.processVideo(
            backgroundVideoPath, videoDuration, mergedAudioDuration, startTime, newWidth, newHeight, mergedSubtitlesPath, image_stream=image_stream, imageDuration=titleAudioDuration)

        self.mergeAudioVideo(video, mergedAudio, outputVideoPath)

        # Delete temp files
        if mergedSubtitlesPath is not None:
            os.remove(mergedSubtitlesPath)

        return outputVideoPath

    def mergeAudio(self, titleAudioPath, descriptionAudioPath):
        titleAudio = ffmpeg.input(titleAudioPath)
        descriptionAudio = ffmpeg.input(descriptionAudioPath)
        # Generate a 1-second silence
        # silence = ffmpeg.input('anullsrc=r=44100:cl=stereo', t=1) -----------------------------------
        # Concatenate the title and content audio files
        audio_stream = ffmpeg.concat(
            titleAudio, descriptionAudio, v=0, a=1)
        return audio_stream

    def mergeSubtitles(self, titleSubtitlesPath, descriptionSubtitlesPath, titleAudioDuration, hasImage):
        if descriptionSubtitlesPath is None or titleSubtitlesPath is None:
            return None

        def add_time_offset(time_str, offset):
            h, m, s_ms = map(float, time_str.replace(',', '.').split(':'))
            total_seconds = h * 3600 + m * 60 + s_ms
            total_seconds += offset
            new_h = int(total_seconds // 3600)
            total_seconds %= 3600
            new_m = int(total_seconds // 60)
            new_s_ms = total_seconds % 60
            return f"{new_h:02d}:{new_m:02d}:{new_s_ms:06.3f}".replace('.', ',')

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.srt')
        temp_path = temp_file.name

        with open(descriptionSubtitlesPath, 'r') as f2:
            lines2 = f2.readlines()

        # Adjust the timestamps in the description file
        new_lines2 = []
        for line in lines2:
            if '-->' in line:
                parts = line.split(' ')
                start_time, end_time = parts[0], parts[2]
                start_time = add_time_offset(start_time, titleAudioDuration)
                end_time = add_time_offset(end_time, titleAudioDuration)
                new_line = f"{start_time} --> {end_time}\n"
                new_lines2.append(new_line)
            else:
                new_lines2.append(line)

        # If hasImage is false, include the title subtitles
        if not hasImage:
            with open(titleSubtitlesPath, 'r') as f1:
                lines1 = f1.readlines()
            with open(temp_path, 'w') as merged:
                merged.writelines(lines1 + new_lines2)
        else:
            with open(temp_path, 'w') as merged:
                merged.writelines(new_lines2)

        return temp_path

    def getAudioDuration(self, ttsAudioPath):
        probe = ffmpeg.probe(ttsAudioPath)
        return float(probe['streams'][0]['duration'])

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

    def processVideo(self, backgroundVideoPath, videoDuration, audioDuration, startTime, newWidth, newHeight, subtitlesPath, image_stream=None, imageDuration=0):
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
                video, image_stream, x='(W-w)/2', y='(H-h)/2', enable=f'between(t,0,{imageDuration})')

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
