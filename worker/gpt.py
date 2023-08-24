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

    def expandAcronymsAndAbbreviations(self, text, language="english", gender="M"):
        if gender == "M":
            gender = "male"
        else:
            gender = "female"
        sharedInstructions = "Expand Reddit related acronyms in the text, and correct grammar mistakes. Don't alter curse words or swearing. Replace slashes and dashes with the appropriate word. Add punctuation as necessary for smooth speech flow. Only respond with the modified (or unmodified if no changes were made) text. Do not include any other information."

        if language != "english":
            instructions = f"Translate the following Reddit post to {language}. The speakers gender is {gender}. Then {sharedInstructions}. Moreover, replace all non-letter characters with their equivalent word or letter representation in the target language. No numerical characters should remain in the text."
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

    def moderationCheckPassed(self, text):
        response = openai.Moderation.create(
            input=text
        )
        output = response["results"][0]
        if output == True:  # True means the text was flagged as being against OpenAI Policy
            print("Moderation check failed")
            return False
        else:
            print("Moderation check passed")
            return True
