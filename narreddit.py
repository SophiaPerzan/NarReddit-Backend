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
        self.scraper = Scraper(env)
        self.tts = TTS(env)
        self.forcedAligner = ForcedAligner(env['GENTLE_URL'])
        self.videoGen = VideoGenerator(env)
        self.gpt = GPT(env)

    def scrapePost(self, params):
        postTitle, postContent = self.scraper.getHotPosts(params)
        print(f"Scraped post: {postContent}")
        return postTitle, postContent

    def editPostForTTS(self, postContent):
        pass

    def generateAudio(self, editedPost, gender, language):
        audioFile = self.tts.createAudio(editedPost, gender, language)
        print(f"Created audio file: {audioFile}")
        return audioFile

    def createSubtitles(self, editedPost, audioFile):
        subtitlesPath = 'tts-audio-files/subtitles.srt'
        subtitleText = self.gpt.getSubtitles(editedPost)
        self.forcedAligner.align(audioFile, subtitleText, subtitlesPath)
        return subtitlesPath

    def generateVideo(self, audioFile, subtitlesPath, params, language):
        outputPath = os.path.join('output', f"{language}.mp4")
        videoFile = self.videoGen.generateVideo(
            audioFile, outputPath, 'background-videos', subtitlesPath, params)

        if videoFile:
            print(f"Created output video file at: {videoFile}")
        else:
            print("Failed to create output video file")
        return videoFile

    def createVideo(self, params):
        postTitle, postContent = self.scrapePost(params)
        languages = params['LANGUAGES'].lower().split(',')
        gender = self.gpt.getGender(postContent)
        videos = []

        for language in languages:
            editedPost = self.gpt.expandAcronymsAndAbbreviations(
                postContent, language)
            audioFile = self.generateAudio(editedPost, gender, language)

            if params['SUBTITLES'].upper() == 'TRUE' and language == 'english':
                subtitlesPath = self.createSubtitles(editedPost, audioFile)
            else:
                subtitlesPath = None

            videos.append(self.generateVideo(
                audioFile, subtitlesPath, params, language))
        return videos
