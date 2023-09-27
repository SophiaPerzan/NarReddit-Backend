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

    def generateAudio(self, editedPost, gender, language, filePrefix, ttsEngine="GOOGLE", key=""):
        match ttsEngine:
            case "ELEVENLABS":
                audioFile = self.elevenlabsTTS.createAudio(
                    editedPost, gender, language, filePrefix, key=key)
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

    def generateVideo(self, titleAudioFile, descriptionAudioFile, titleSubtitlesPath, descriptionSubtitlesPath, params, language, filePrefix):
        outputPath = os.path.join('shared', f"{language}-{filePrefix}.mp4")
        if params.get('USER_ID') is not None:
            videoDirectory = os.path.join(
                'shared', 'background-videos', params['USER_ID'])
        else:
            videoDirectory = os.path.join('shared', 'background-videos')

        if params['BG_VIDEO_FILENAME'] == 'RANDOM':
            bgVideoPath = self.getRandomMP4(videoDirectory)
        else:
            bgVideoPath = os.path.join(
                videoDirectory, params['BG_VIDEO_FILENAME'])
        videoFile = self.videoGen.generateVideo(
            titleAudioFile, descriptionAudioFile, outputPath, bgVideoPath, titleSubtitlesPath, descriptionSubtitlesPath, params)

        if videoFile:
            print(f"Created output video file at: {videoFile}")
        else:
            print("Failed to create output video file")
        return videoFile

    def getRandomMP4(self, directory):
        # Filter the list to include only .mp4 files
        mp4Files = [entry.path for entry in os.scandir(
            directory) if entry.is_file() and entry.name.endswith('.mp4')]

        # Select a random .mp4 file
        randomMP4 = random.choice(mp4Files)

        return randomMP4

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

            for language in languages:
                editedTitle = self.gpt.expandAcronymsAndAbbreviations(
                    postTitle, language=language, gender=gender)
                editedDescription = self.gpt.expandAcronymsAndAbbreviations(
                    postDescription, language=language, gender=gender)

                titleAudioFile = self.generateAudio(
                    editedTitle, gender, language, f"title-{filePrefix}", ttsEngine, key=key)

                descriptionAudioFile = self.generateAudio(
                    editedDescription, gender, language, f"description-{filePrefix}", ttsEngine, key=key)

                if params['SUBTITLES'] == True:
                    titleSubtitlesPath = self.createSubtitles(
                        editedTitle, titleAudioFile, f"title-{filePrefix}", language)
                    descriptionSubtitlesPath = self.createSubtitles(
                        editedDescription, descriptionAudioFile, f"description-{filePrefix}", language)
                else:
                    titleSubtitlesPath = None
                    descriptionSubtitlesPath = None

                videos.append(self.generateVideo(
                    titleAudioFile, descriptionAudioFile, titleSubtitlesPath, descriptionSubtitlesPath, params, language, filePrefix))

                os.remove(titleAudioFile)
                os.remove(descriptionAudioFile)
                if titleSubtitlesPath:
                    os.remove(titleSubtitlesPath)
                if descriptionSubtitlesPath:
                    os.remove(descriptionSubtitlesPath)
            if params['IMAGE_FILE'] is not None:
                os.remove(params['IMAGE_FILE'])
            return videos

        except Exception as e:
            raise Exception(e)
