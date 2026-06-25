import whisper
import noisereduce as nr
import librosa
import requests

class VoiceHandler:
    def __init__(self):
        # Load the Whisper model for speech-to-text processing
        self.whisperModel = whisper.load_model("base")
        # Define the VOICEVOX engine URL (will be used when Docker is ready)
        self.voicevoxUrl = "http://localhost:50021"

    def removeNoise(self, audioFilePath):
        # Load the audio file as a floating point time series
        audioData, sampleRate = librosa.load(audioFilePath, sr=None)
        
        # Reduce background noise from the audio data to improve recognition accuracy
        cleanAudioData = nr.reduce_noise(y=audioData, sr=sampleRate)
        
        return cleanAudioData

    def convertSpeechToText(self, audioFilePath):
        # Step 1: Apply noise reduction before speech-to-text conversion
        cleanAudio = self.removeNoise(audioFilePath)

        # Step 2: Convert the cleaned audio data to text using Whisper
        transcriptionResult = self.whisperModel.transcribe(cleanAudio)
        
        # Return the extracted text string
        return transcriptionResult["text"]

    def generateVoice(self, text):
        # This method is pre-implemented for future VOICEVOX integration.
        # It requires the VOICEVOX Docker container to be running.
        
        # Step 1: Request audio query generation from VOICEVOX
        params = {"text": text, "speaker": 1}
        queryResponse = requests.post(f"{self.voicevoxUrl}/audio_query", params=params)
        audioQuery = queryResponse.json()
        
        # Step 2: Request synthesis using the generated audio query
        synthesisResponse = requests.post(
            f"{self.voicevoxUrl}/synthesis", 
            params={"speaker": 1}, 
            json=audioQuery
        )
        
        # Return the raw audio binary data
        return synthesisResponse.content