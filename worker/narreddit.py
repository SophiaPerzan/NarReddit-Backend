from os import environ as env
from scraper import Scraper
from elevenlabs_tts import ElevenlabsTTS
from google_tts import GoogleTTS
from videoGen import VideoGenerator
from aeneas_aligner import AeneasAligner
import os
from gpt import GPT


class NarReddit:
    def __init__(self):
        self.scraper = Scraper(env)
        self.googleTTS = GoogleTTS()
        self.elevenlabsTTS = ElevenlabsTTS(env)
        self.aeneasAligner = AeneasAligner()
        self.videoGen = VideoGenerator(env)
        self.gpt = GPT(env)

    def scrapePost(self, params):
        postTitle, postContent = self.scraper.getHotPosts(params)
        print(f"Scraped post: {postContent}")
        return postTitle, postContent

    def editPostForTTS(self, postContent):
        pass

    def generateAudio(self, editedPost, gender, language, filePrefix, ttsEngine="GOOGLE"):
        match ttsEngine:
            case "ELEVENLABS":
                audioFile = self.elevenlabsTTS.createAudio(
                    editedPost, gender, language, filePrefix)
            case "GOOGLE":
                audioFile = self.googleTTS.createAudio(
                    editedPost, gender, language, filePrefix)
            case _:
                audioFile = self.googleTTS.createAudio(
                    editedPost, gender, language, filePrefix)
        print(f"Created audio file: {audioFile}")
        return audioFile

    def createSubtitles(self, editedPost, audioFile, filePrefix, language):
        subtitlesPath = os.path.join(
            'shared', 'tts-audio-files', f'subtitles-{filePrefix}.srt')
        subtitleText = editedPost
        self.aeneasAligner.align(
            audioFile, subtitleText, subtitlesPath, language)
        return subtitlesPath

    def generateVideo(self, audioFile, subtitlesPath, params, language, filePrefix):
        outputPath = os.path.join('shared', f"{language}-{filePrefix}.mp4")
        bgVideoPath = os.path.join('shared', 'background-videos')
        videoFile = self.videoGen.generateVideo(
            audioFile, outputPath, bgVideoPath, subtitlesPath, params)

        if videoFile:
            print(f"Created output video file at: {videoFile}")
        else:
            print("Failed to create output video file")
        return videoFile

    def createVideo(self, params):
        try:
            filePrefix = params['DOC_ID']
            postTitle, postContent = self.scrapePost(params)
            languages = params['LANGUAGES'].lower().split(',')
            if self.gpt.moderationCheckPassed(postContent) == False:
                raise Exception("Post failed moderation check")
            gender = self.gpt.getGender(postContent)
            videos = []
            ttsEngine = params['TTS_ENGINE'].upper()

            for language in languages:
                editedPost = self.gpt.expandAcronymsAndAbbreviations(
                    postContent, language)
                audioFile = self.generateAudio(
                    editedPost, gender, language, filePrefix, ttsEngine)

                if params['SUBTITLES'] == True:
                    subtitlesPath = self.createSubtitles(
                        editedPost, audioFile, filePrefix, language)
                else:
                    subtitlesPath = None

                videos.append(self.generateVideo(
                    audioFile, subtitlesPath, params, language, filePrefix))
                os.remove(audioFile)
                if subtitlesPath:
                    os.remove(subtitlesPath)
            return videos

        except Exception as e:
            raise Exception(e)
