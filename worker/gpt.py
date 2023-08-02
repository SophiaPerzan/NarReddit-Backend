import openai


class GPT:
    def __init__(self, env) -> None:
        self.env = env
        openai.api_key = env['OPENAI_API_KEY']
        self.model = "gpt-3.5-turbo"
        if (env['USE_GPT_4'].upper() == 'TRUE'):
            self.model = "gpt-4"

    def getGender(self, text):
        instructions = "From the given text, determine the poster's gender. Use the context provided by the text. If the gender is ambiguous, reply with the most probable gender. Respond with a single letter: 'M' for Male or 'F' for Female."
        return openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": text}
            ],
            temperature=0.2
        ).choices[0].message.content

    def expandAcronymsAndAbbreviations(self, text, language="english"):
        sharedInstructions = "Expand the abbreviations and acronyms in the text, correct grammar mistakes, and enhance the overall readability. Since the output will be used as input for a text-to-speech program, ensure it can be processed easily. Add punctuation as necessary for smooth speech flow. You can leave commonly understood acronyms and abbreviations as they are."

        if language != "english":
            instructions = f"Translate the following Reddit post to {language}, then {sharedInstructions}. Moreover, replace all non-letter characters with their equivalent word or letter representation in the target language. No numerical characters should remain in the text."
        else:
            instructions = f"Given the following Reddit post, {sharedInstructions}"

        return openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": text}
            ],
            temperature=0.1
        ).choices[0].message.content

    def getSubtitles(self, text):
        instructions = "Given the following transcript, replace all non-letter characters and numbers with their corresponding word or letter representation."
        return openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": text}
            ],
            temperature=0.1
        ).choices[0].message.content
