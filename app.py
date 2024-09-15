import streamlit as st

from pydub import AudioSegment
import googletrans
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
import googletrans

import time
import speech_recognition as sr

def transcribe_custom(audio_path,src_lang,tar_lang):
    recognizer = sr.Recognizer()

    # Convert audio to WAV format using pydub (since SpeechRecognition works best with WAV files)
    audio = AudioSegment.from_file(audio_path)
    audio = audio.set_channels(1)  # Ensure mono channel
    audio = audio.set_frame_rate(16000)  # Ensure frame rate is 16000 Hz
    translator = googletrans.Translator()

    # Split the audio into chunks
    chunk_duration_ms = 10000  # 10 sec per chunk
    chunks = [audio[i:i + chunk_duration_ms] for i in range(0, len(audio), chunk_duration_ms)]

    final_transcription=''
    final_translation=''

    for i, chunk in enumerate(chunks):
        chunk_filename = f"chunk.wav"
        chunk.export(chunk_filename, format="wav")

        # Use the SpeechRecognition library to process the WAV file
        with sr.AudioFile(chunk_filename) as source:
            audio_data = recognizer.record(source)

        try:
            text = recognizer.recognize_google(audio_data, language=src_lang)
            translation = translator.translate(text, dest=tar_lang)
            final_transcription+=text
            final_translation+=translation.text
            # print(translation.text)
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand the audio")
    return final_transcription,final_translation



st.title("Audio Transcription and Translation App")

# Audio file uploader
audio_file = st.file_uploader("Upload an audio file", type=["mp3", "wav", "ogg", "flac","m4a"])

# Language selector
languages = googletrans.LANGUAGES
language_options = list(languages.values())
selected_lang_src = st.selectbox("Select the translation language source", language_options)
selected_lang_tar = st.selectbox("Select the translation language target", language_options)

# Button to trigger transcription
if st.button("Transcribe and Translate"):
    if audio_file is not None:
        # Save the uploaded file temporarily
        with open("temp_audio_file", "wb") as f:
            f.write(audio_file.getbuffer())

        # Get the language code for the selected language
        selected_lang_code_src = list(languages.keys())[language_options.index(selected_lang_src)]
        selected_lang_code_tar = list(languages.keys())[language_options.index(selected_lang_tar)]

        # Transcribe and translate
        transcription, translation = transcribe_custom("temp_audio_file", selected_lang_code_src,selected_lang_code_tar)

        # Display results
        st.subheader("Transcription:")
        st.write(transcription)

        st.subheader("Translation:")
        st.write(translation)
    else:
        st.error("Please upload an audio file.")
