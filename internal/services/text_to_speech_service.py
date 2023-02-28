from google.cloud import texttospeech

class TextToSpeechService:
    def __init__(self, voice = None, language_code = None) -> None:
        # text = data.text
        self.voice = voice if voice is not None else 'en-US-Wavenet-A'
        self.language_code = language_code if language_code is not None else 'en-US'

    def audio_generator(response):
        for chunk in response.audio_content:
            print('\n\n\n\n' + str(chunk))
            yield bytes(chunk)

    def talk(self, text):
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=text)

        voice = texttospeech.VoiceSelectionParams(
            language_code=self.language_code, name=self.voice
        )

        # Select the type of audio file you want returned
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MULAW,
            sample_rate_hertz=8000
        )

        # Perform the text-to-speech request on the text input with the selected
        # voice parameters and audio file type
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        return response.audio_content


