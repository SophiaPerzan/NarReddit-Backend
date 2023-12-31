from os import environ as env
from scraper import Scraper
from elevenlabs_tts import ElevenlabsTTS
from google_tts import GoogleTTS
from videoGen import VideoGenerator
from aeneas_aligner import AeneasAligner
import os
from gpt import GPT
import random


class NarReddit:
    def __init__(self, bucket):
        self.bucket = bucket
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

    def generateAudio(self, editedPost, gender, language, filePrefix, ttsEngine="GOOGLE", key="", voice=None):
        match ttsEngine:
            case "ELEVENLABS":
                audioFile = self.elevenlabsTTS.createAudio(
                    editedPost, gender, language, filePrefix, key=key, voice=voice)
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
            'temp', 'tts-audio-files', f'subtitles-{filePrefix}.srt')
        os.makedirs(os.path.dirname(subtitlesPath), exist_ok=True)
        subtitleText = editedPost
        self.aeneasAligner.align(
            audioFile, subtitleText, subtitlesPath, language)
        return subtitlesPath

    def generateVideo(self, bgVideoPath, titleAudioFile, descriptionAudioFile, titleSubtitlesPath, descriptionSubtitlesPath, params, language, filePrefix):
        outputPath = os.path.join('temp', f"{language}-{filePrefix}.mp4")
        os.makedirs(os.path.dirname(outputPath), exist_ok=True)

        videoFile = self.videoGen.generateVideo(
            titleAudioFile, descriptionAudioFile, outputPath, bgVideoPath, titleSubtitlesPath, descriptionSubtitlesPath, params)

        if videoFile:
            print(f"Created output video file at: {videoFile}")
        else:
            print("Failed to create output video file")
        return videoFile

    def createVideo(self, params):
        try:
            filePrefix = params['DOC_ID']

            if params['CONTENT_ORIGIN'] == 'scraped':
                postTitle, postDescription = self.scrapePost(params)
            elif params['CONTENT_ORIGIN'] == 'text':
                postTitle = params['TITLE']
                postDescription = params['DESCRIPTION']
            postTitleAndDescription = postTitle + '\n' + postDescription

            languages = params['LANGUAGES'].lower().split(',')
            if self.gpt.moderationCheckPassed(postTitleAndDescription) == False:
                raise Exception("Post failed moderation check")
            gender = self.gpt.getGender(postTitleAndDescription)
            videos = []
            ttsEngine = params['TTS_ENGINE'].upper()
            key = ''
            if params.get('ELEVENLABS_API_KEY') is not None:
                key = params['ELEVENLABS_API_KEY']
            voice = None
            if params.get('ELEVENLABS_VOICE') is not None:
                voice = params['ELEVENLABS_VOICE']

            blob = self.bucket.blob(params['BG_VIDEO_FILENAME'])
            bgVideoPath = os.path.join(
                'temp', f"{os.path.basename(params['BG_VIDEO_FILENAME'])}")
            os.makedirs(os.path.dirname(bgVideoPath), exist_ok=True)
            blob.download_to_filename(bgVideoPath)

            for language in languages:
                editedTitle = self.gpt.expandAcronymsAndAbbreviations(
                    postTitle, language=language, gender=gender)
                editedDescription = self.gpt.expandAcronymsAndAbbreviations(
                    postDescription, language=language, gender=gender)

                titleAudioFile = self.generateAudio(
                    editedTitle, gender, language, f"title-{filePrefix}", ttsEngine, key=key, voice=voice)

                descriptionAudioFile = self.generateAudio(
                    editedDescription, gender, language, f"description-{filePrefix}", ttsEngine, key=key, voice=voice)

                if params['SUBTITLES'] == True:
                    titleSubtitlesPath = self.createSubtitles(
                        editedTitle, titleAudioFile, f"title-{filePrefix}", language)
                    descriptionSubtitlesPath = self.createSubtitles(
                        editedDescription, descriptionAudioFile, f"description-{filePrefix}", language)
                else:
                    titleSubtitlesPath = None
                    descriptionSubtitlesPath = None

                videos.append(self.generateVideo(
                    bgVideoPath, titleAudioFile, descriptionAudioFile, titleSubtitlesPath, descriptionSubtitlesPath, params, language, filePrefix))

                os.remove(titleAudioFile)
                os.remove(descriptionAudioFile)
                if titleSubtitlesPath:
                    os.remove(titleSubtitlesPath)
                if descriptionSubtitlesPath:
                    os.remove(descriptionSubtitlesPath)
            if params['IMAGE_FILE'] is not None:
                os.remove(params['IMAGE_FILE'])
            os.remove(bgVideoPath)
            return videos

        except Exception as e:
            raise Exception(e)
