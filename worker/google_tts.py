from google.cloud import texttospeech
import os


class GoogleTTS:
    def __init__(self):
        # Instantiates a client
        self.client = texttospeech.TextToSpeechClient()

    def createAudio(self, text, gender, language, filePrefix):

        if gender == "M":
            voiceNames = {"en-US": "en-US-Standard-J",
                          "es-US": "es-US-Standard-C", "fr-FR": "fr-FR-Standard-B", "it-IT": "it-IT-Standard-D", "de-DE": "de-DE-Standard-B", "pt-BR": "pt-BR-Standard-B", "pl-PL": "pl-PL-Standard-B", "hi-IN": "hi-IN-Standard-C"}
            voiceGender = texttospeech.SsmlVoiceGender.MALE
        else:
            voiceNames = {"en-US": "en-US-Standard-H",
                          "es-US": "es-US-Standard-A", "fr-FR": "fr-FR-Standard-A", "it-IT": "it-IT-Standard-B", "de-DE": "de-DE-Standard-F", "pt-BR": "pt-BR-Standard-C", "pl-PL": "pl-PL-Standard-E", "hi-IN": "hi-IN-Standard-D"}
            voiceGender = texttospeech.SsmlVoiceGender.FEMALE

        match language:
            case "english":
                langCode = "en-US"
            case "spanish":
                langCode = "es-US"
            case "french":
                langCode = "fr-FR"
            case "italian":
                langCode = "it-IT"
            case "german":
                langCode = "de-DE"
            case "portuguese":
                langCode = "pt-BR"
            case "polish":
                langCode = "pl-PL"
            case "hindi":
                langCode = "hi-IN"
            case _:
                langCode = "en-US"

        # Build the voice request, select the language code, name, and voice gender
        voice = texttospeech.VoiceSelectionParams(
            language_code=langCode, name=voiceNames[langCode], ssml_gender=voiceGender
        )
        # Set the text input to be synthesized
        synthesis_input = texttospeech.SynthesisInput(text=text)
        # Select the type of audio file you want returned
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        # Perform the text-to-speech request on the text input with the selected
        # voice parameters and audio file type
        response = self.client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        fileName = os.path.join(
            'shared', 'tts-audio-files', f'{language}-{filePrefix}.mp3')
        # The response's audio_content is binary.
        with open(f"{fileName}", "wb") as out:
            # Write the response to the output file.
            out.write(response.audio_content)
        return fileName
