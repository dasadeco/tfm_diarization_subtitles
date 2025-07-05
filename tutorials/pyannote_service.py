from pyannote.audio import Pipeline, Model, Inference
from scipy.spatial.distance import cdist
import torch
from pydub import AudioSegment
import os
from tempfile import TemporaryDirectory

from core.common.config import Config
from core.common.logger import use_logger

config = Config.get_instance()

logger = use_logger(__name__)


class PyannoteService:
    def __init__(self):
        self.pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=config.hugging_face.token,
        )
        self.pipeline.to(torch.device("cuda"))

        self.embedding_model = Model.from_pretrained(
            "pyannote/embedding", use_auth_token=config.hugging_face.token
        )
        self.embedding_inference = Inference(self.embedding_model, window="whole")
        self.embedding_inference.to(torch.device("cuda"))

    def diarize(self, audio_file: str):
        diarization = self.pipeline(audio_file)

        return [
            {"timestamp": (turn.start, turn.end), "speaker": speaker}
            for turn, _, speaker in diarization.itertracks(yield_label=True)
        ]

    def create_embedding(self, audio_file: str):
        return self.embedding_inference(audio_file).reshape(1, -1)

    def calculate_embeddings_distance(self, embedding1, embedding2):
        return cdist(embedding1, embedding2, metric="cosine")[0, 0]

    def update_speaker_voice(self, audio_file, speakers, speaker_dir):
        original_audio = AudioSegment.from_wav(audio_file)
        chunk_size_ms = 3 * 1000  # 5 seconds in milliseconds

        embeddings = {}
        for entry in speakers:
            start, end = entry["timestamp"]
            speaker = entry["speaker"]

            # Process each 5-second chunk
            chunk_start = start
            while chunk_start < end:
                chunk_end = min(chunk_start + chunk_size_ms, end)
                segment = original_audio[chunk_start * 1000 : chunk_end * 1000]

                speaker_path = os.path.join(speaker_dir, f"{speaker}_{chunk_start}-{chunk_end}.wav")

                if os.path.exists(speaker_path):
                    existing_audio = AudioSegment.from_wav(speaker_path)
                    combined_audio = existing_audio + segment
                    if len(combined_audio) > chunk_size_ms:
                        combined_audio = combined_audio[-chunk_size_ms:]
                    new_audio = combined_audio
                else:
                    if len(segment) > chunk_size_ms:
                        segment = segment[-chunk_size_ms:]
                    new_audio = segment

                # Extend the audio chunk to prevent embedding error
                if len(new_audio) < chunk_size_ms:
                    silence = AudioSegment.silent(chunk_size_ms - len(new_audio))
                    new_audio = silence + new_audio

                new_audio.export(speaker_path, format="wav")
                embeddings[f"{speaker}_{chunk_start}-{chunk_end}"] = self.create_embedding(speaker_path)

                chunk_start = chunk_end

        return embeddings

    def identify_each_chunk_speaker(self, audio_path, speakers, voices_embeddings):
        audio = AudioSegment.from_wav(audio_path)
        result = []
        distances = {}

        chunk_size_ms = 3 * 1000  # 5 seconds in milliseconds

        with TemporaryDirectory() as chunks_dir:
            for entry in speakers:
                timestamp = entry["timestamp"]
                speaker = entry["speaker"]
                start, end = timestamp

                chunk_start = start
                while chunk_start < end:
                    chunk_end = min(chunk_start + chunk_size_ms / 1000, end)  # Convert chunk size to seconds
                    chunk_start_ms = int(chunk_start * 1000)
                    chunk_end_ms = int(chunk_end * 1000)

                    audio_chunk_path = os.path.join(
                        chunks_dir, f"{os.path.basename(audio_path)}_{chunk_start_ms}-{chunk_end_ms}.wav"
                    )
                    audio_chunk = audio[chunk_start_ms:chunk_end_ms]

                    # Extend the audio chunk to prevent embedding error
                    if chunk_end - chunk_start < 1:
                        silence = AudioSegment.silent(int((1 - (chunk_end - chunk_start)) * 1000 / 2))
                        audio_chunk = silence + audio_chunk + silence

                    audio_chunk.export(audio_chunk_path, format="wav")

                    chunk_key = f"{chunk_start_ms}-{chunk_end_ms}"  # Use chunk start and end times as key
                    distances[chunk_key] = {}
                    for voice in voices_embeddings:
                        distances[chunk_key][voice] = self.calculate_embeddings_distance(
                            voices_embeddings[voice],
                            self.create_embedding(audio_chunk_path),
                        )

                    # Set distance to 0.5 if there's no example of the speaker's voice
                    if not distances[chunk_key].get(speaker):
                        distances[chunk_key][speaker] = 0.5

                    chunk_start = chunk_end

        logger.info("DISTANCES\n" + str(distances))

        for entry in speakers:
            timestamp = entry["timestamp"]
            start, end = timestamp

            # Calculate average distance for the chunk
            chunk_key = f"{chunk_start_ms}-{chunk_end_ms}"
            avg_distance = sum(distances[chunk_key].values()) / len(distances[chunk_key])

            # Determine speaker based on average distance
            if avg_distance > 0.65:
                speaker = f"SPEAKER_{len(voices_embeddings) + 1:02}"
            else:
                speaker = min(distances[chunk_key], key=distances[chunk_key].get)

            result.append({"timestamp": timestamp, "speaker": speaker})

        return result