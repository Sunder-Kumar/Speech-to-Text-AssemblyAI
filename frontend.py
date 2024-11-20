from gtts import gTTS
import streamlit as st
import requests
import time
import os

if not os.path.exists("temp"):
    os.makedirs("temp")

UPLOAD_URL = "http://127.0.0.1:5000/upload"
TRANSCRIPTION_URL = "http://127.0.0.1:5000/transcription/"

st.title("Sophisticated Speech-to-Text Application")
st.write("Upload your audio files and let AssemblyAI's Universal-2 transcribe them!")

audio_file = st.file_uploader("Upload an audio file", type=["mp3", "wav", "m4a"])

language_code = st.selectbox("Select the language:", ["en", "hi", "es", "fr", "de", "it", "pt"])

enable_speaker_labels = st.checkbox("Enable Speaker Diarization")

if audio_file is not None:
    local_path = f"temp/{audio_file.name}"
    with open(local_path, "wb") as f:
        f.write(audio_file.read())

    st.write("File uploaded successfully! Sending it for transcription...")

    with open(local_path, "rb") as f:
        files = {"file": f}
        data = {"language_code": language_code, "enable_speaker_labels": str(enable_speaker_labels)}
        response = requests.post(UPLOAD_URL, files=files, data=data)

    if response.status_code == 200:
        data = response.json()
        transcript_id = data.get("transcript_id")

        status = "queued"

        with st.spinner("Transcription in progress... Please wait."):
            while status not in ["completed", "failed"]:
                time.sleep(5) 
                result = requests.get(f"{TRANSCRIPTION_URL}{transcript_id}").json()
                status = result.get("status", "failed")

        if status == "completed":
            st.write("**Transcription Completed!**")

            if enable_speaker_labels and "utterances" in result:
                st.write("**Speaker Diarization:**")
                for utterance in result["utterances"]:
                    start_time = utterance.get("start", 0) / 1000 
                    end_time = utterance.get("end", 0) / 1000
                    st.write(f"Speaker {utterance.get('speaker', 'Unknown')} - "
                             f"[{start_time:.2f}s to {end_time:.2f}s]: {utterance.get('text', '')}")
            else:
                st.write("**Transcribed Text with Timestamps:**")
                st.write(result.get("text", ""))

                for word in result.get("words", []):
                    start_time = word.get("start", 0) / 1000 
                    end_time = word.get("end", 0) / 1000
                    st.write(f"{word['text']} - Start: {start_time:.2f}s, End: {end_time:.2f}s")

            # Option to download the transcription
            st.download_button(
                label="Download Transcription",
                data=result.get("text", ""),
                file_name="transcription.txt",
                mime="text/plain",
            )
        elif status == "failed":
            st.error("Transcription failed. Please try again.")
    else:
        st.error("Error uploading file. Please try again.")
