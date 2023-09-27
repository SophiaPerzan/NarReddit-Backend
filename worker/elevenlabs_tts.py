from elevenlabs import set_api_key, generate, voices, save
import os


class ElevenlabsTTS:
    def __init__(self, env):
        self.env = env
        set_api_key(env['ELEVENLABS_API_KEY'])
        self.voices = voices()
        self.Paola = self.findVoice(self.voices, "Paola")
        self.Arthur = self.findVoice(self.voices, "Arthur")
        self.Matthew = self.findVoice(self.voices, "Matthew")
        self.Grace = self.findVoice(self.voices, "Grace")

    def findVoice(self, voices, name):
        for voice in voices:
            if voice.name == name:
                return voice
        return None

    def createAudio(self, text, gender, language, filePrefix, key=""):
        customApiKey = False
        if key != "":
            self.setAPIKey(key)
            customApiKey = True
        if customApiKey:
            voice = self.Grace
            if gender == "M":
                voice = self.Matthew
        else:
            voice = self.Paola
            if gender == "M":
                voice = self.Arthur

        if language == "english":
            audio = generate(
                text, voice=voice, model="eleven_monolingual_v1")
            fileName = os.path.join(
                'shared', 'tts-audio-files', f'english-{filePrefix}.mp3')
        else:
            audio = generate(
                text, voice=voice, model="eleven_multilingual_v2")
            fileName = os.path.join(
                'shared', 'tts-audio-files', f'{language}-{filePrefix}.mp3')
        save(audio, fileName)
        return fileName

    def setAPIKey(self, key):
        set_api_key(key)
