import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import av
from pydub import AudioSegment
import io
import numpy as np
import googletrans
import speech_recognition as sr
import os

class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.audio_buffer = []

    def recv(self, frame: av.AudioFrame):
        # Convert audio frame to numpy array
        audio_data = frame.to_ndarray()
        self.audio_buffer.append(audio_data)
        return frame

    def get_audio_data(self):
        # Combine all audio frames into one numpy array
        if self.audio_buffer:
            audio_data = np.concatenate(self.audio_buffer, axis=0)
            return audio_data
        return None

def save_audio(audio_data, file_path):
    # Save the numpy array as a WAV file
    with io.BytesIO() as wav_buffer:
        wav_segment = AudioSegment(
            data=audio_data.tobytes(),
            sample_width=2,  # 16-bit audio
            frame_rate=16000,
            channels=1
        )
        wav_segment.export(wav_buffer, format="wav")
        with open(file_path, "wb") as f:
            f.write(wav_buffer.getvalue())

def transcribe_custom(audio_path, src_lang, tar_lang):
    recognizer = sr.Recognizer()
    audio = AudioSegment.from_file(audio_path)
    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)
    translator = googletrans.Translator()
    chunk_duration_ms = 10000
    chunks = [audio[i:i + chunk_duration_ms] for i in range(0, len(audio), chunk_duration_ms)]
    final_transcription = ''
    final_translation = ''
    for i, chunk in enumerate(chunks):
        chunk_filename = f"chunk_{i}.wav"
        chunk.export(chunk_filename, format="wav")
        with sr.AudioFile(chunk_filename) as source:
            audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data, language=src_lang)
            translation = translator.translate(text, dest=tar_lang)
            final_transcription += text + ' '
            final_translation += translation.text + ' '
        except sr.RequestError as e:
            st.error(f"Could not request results from Google Speech Recognition service; {e}")
        except sr.UnknownValueError:
            st.error("Google Speech Recognition could not understand the audio")
    return final_transcription, final_translation

st.title("Audio Transcription and Translation App")

# Audio recorder using streamlit-webrtc
audio_processor = AudioProcessor()
webrtc_ctx = webrtc_streamer(
    key="audio_recorder",
    mode="sendrecv",
    audio_processor_factory=lambda: audio_processor,
    media_stream_constraints={"audio": True}
)

if st.button("Save Recorded Audio"):
    audio_data = audio_processor.get_audio_data()
    if audio_data is not None:
        save_audio(audio_data, "recorded_audio_file.wav")
        st.write("Audio recorded and saved as 'recorded_audio_file.wav'.")
    else:
        st.write("No audio recorded yet.")

# Audio file uploader
uploaded_file = st.file_uploader("Upload an audio file", type=["mp3", "wav", "ogg", "flac", "m4a"])

# Language selector
languages = googletrans.LANGUAGES
language_options = list(languages.values())
selected_lang_src = st.selectbox("Select the translation language source", language_options)
selected_lang_tar = st.selectbox("Select the translation language target", language_options)

# Button to trigger transcription and translation
if st.button("Transcribe and Translate"):
    if uploaded_file is not None:
        # Save the uploaded file temporarily
        with open("temp_audio_file", "wb") as f:
            f.write(uploaded_file.getbuffer())
        audio_path = "temp_audio_file"
    else:
        audio_path = "recorded_audio_file.wav"  # Use recorded file if uploaded file is not provided

    if os.path.exists(audio_path):
        selected_lang_code_src = list(languages.keys())[language_options.index(selected_lang_src)]
        selected_lang_code_tar = list(languages.keys())[language_options.index(selected_lang_tar)]
        transcription, translation = transcribe_custom(audio_path, selected_lang_code_src, selected_lang_code_tar)
        st.subheader("Transcription:")
        st.write(transcription)
        st.subheader("Translation:")
        st.write(translation)
    else:
        st.error("Please upload an audio file or record audio.")
