from os import environ as env
from dotenv import load_dotenv
from scraper import Scraper
from tts import TTS
from videoGen import VideoGenerator
from forcedAligner import ForcedAligner
import os
from gpt import GPT


class NarReddit:
    def __init__(self):
        load_dotenv()
        self.env = env

    def scrapePost(self, params):
        scraper = Scraper(self.env)
        postTitle, postContent = scraper.getHotPosts(params)
        print(f"Scraped post: {postContent}")
        return postTitle, postContent

    def generateAudio(self, editedPost, gender, language):
        tts = TTS(self.env)
        audioFile = tts.createAudio(editedPost, gender, language)
        print(f"Created audio file: {audioFile}")
        return audioFile

    def createSubtitles(self, editedPost, audioFile):
        subtitlesPath = 'tts-audio-files/subtitles.srt'
        forcedAligner = ForcedAligner(self.env['GENTLE_URL'])
        subtitleText = gpt.getSubtitles(editedPost)
        forcedAligner.align(audioFile, subtitleText, subtitlesPath)
        return subtitlesPath

    def generateVideo(self, audioFile, subtitlesPath, params, language):
        videoGen = VideoGenerator(self.env)
        outputPath = os.path.join('output', f"{language}.mp4")
        videoFile = videoGen.generateVideo(
            audioFile, outputPath, 'background-videos', subtitlesPath, params)

        if videoFile:
            print(f"Created output video file at: {videoFile}")
        else:
            print("Failed to create output video file")
        return videoFile

    def createVideo(self, params):
        postTitle, postContent = self.scrapePost(params)
        languages = params['LANGUAGES'].lower().split(',')
        gpt = GPT(self.env)
        gender = gpt.getGender(postContent)

        for language in languages:
            editedPost = gpt.expandAcronymsAndAbbreviations(
                postContent, language)
            audioFile = self.generateAudio(editedPost, gender, language)

            if params['SUBTITLES'].upper() == 'TRUE' and language == 'english':
                subtitlesPath = self.createSubtitles(editedPost, audioFile)
            else:
                subtitlesPath = None

            self.generateVideo(audioFile, subtitlesPath, params, language)
