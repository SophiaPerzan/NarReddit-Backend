from aeneas.executetask import ExecuteTask
from aeneas.task import Task
from aeneas.task import TaskConfiguration
import tempfile
import os


class AeneasAligner:
    def align(self, audio_file, text_string, subtitles_file, language, max_length=13):
        # Break the text string into phrases
        phrases = self.break_into_phrases(text_string, max_length)

        # Convert relative file paths to absolute
        audio_file = os.path.abspath(audio_file)
        subtitles_file = os.path.abspath(subtitles_file)

        # Create a temporary text file and write the phrases into it
        with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.txt') as text_file:
            for phrase in phrases:
                text_file.write(phrase + "\n")
            text_path = text_file.name

        # Get the language code
        match language:
            case "english":
                language_code = "en"
            case "spanish":
                language_code = "es"
            case "french":
                language_code = "fr"
            case "italian":
                language_code = "it"
            case "german":
                language_code = "de"
            case "portuguese":
                language_code = "pt"
            case "polish":
                language_code = "pl"
            case "hindi":
                language_code = "hi"
            case _:
                language_code = "en"

        # Create a TaskConfiguration object
        config_string = u"task_language=" + language_code + \
            "|is_text_type=plain|os_task_file_format=srt"

        # Create a Task object
        task = Task(config_string=config_string)
        task.audio_file_path_absolute = audio_file
        task.text_file_path_absolute = text_path
        task.sync_map_file_path_absolute = subtitles_file

        # Process the Task
        ExecuteTask(task).execute()

        task.output_sync_map_file()

        # Delete the temporary text file
        os.remove(text_path)

        return subtitles_file

    def break_into_phrases(self, text, max_length):
        phrases = []
        words = text.split()
        current_phrase = ""

        for word in words:
            if len(current_phrase) + len(word) > max_length and len(current_phrase) > 0 or current_phrase.endswith(('.', '?', '!', ',', ':', ';', '¡', '¿', '»')):
                phrases.append(current_phrase.strip())
                current_phrase = ""
            current_phrase += " " + word

        if current_phrase:
            phrases.append(current_phrase.strip())

        return phrases
