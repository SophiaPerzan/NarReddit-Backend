from os import environ as env
from dotenv import load_dotenv
from scraper import Scraper
from tts import TTS
from videoGen import VideoGenerator
from forcedAligner import ForcedAligner
import os
from gpt import GPT


class NarReddit:
    def __init__(self) -> None:
        pass

    def createVideo(self, params):

        load_dotenv()

        scraper = Scraper(env)
        post = scraper.getHotPosts(params)
        postTitle = post[0]
        postTitleAndText = post[1]
        print("Scraped post: "+postTitleAndText)

        languages = params['LANGUAGES'].split(',')
        languages = [lang.lower() for lang in languages]

        gpt = GPT(env)
        gender = gpt.getGender(postTitleAndText)

        for language in languages:
            editedPost = gpt.expandAcronymsAndAbbreviations(
                postTitleAndText, language)

            tts = TTS(env)
            audioFile = tts.createAudio(editedPost, gender, language)
            print("Created audio file: " + audioFile)

            if params['SUBTITLES'].upper() == 'TRUE' and language == 'english':
                subtitlesPath = 'tts-audio-files/subtitles.srt'
                forcedAligner = ForcedAligner(
                    env['GENTLE_URL'])
                subtitleText = gpt.getSubtitles(editedPost)
                forcedAligner.align(audioFile, subtitleText, subtitlesPath)
            else:
                subtitlesPath = None
            videoGen = VideoGenerator(env)
            directory = 'background-videos'
            outputPath = os.path.join('output', language+'.mp4')
            videoFile = videoGen.generateVideo(
                audioFile, outputPath, directory, subtitlesPath, params)
            if (videoFile != False):
                print("Created output video file at: " + videoFile)
            else:
                print("Failed to create output video file")
