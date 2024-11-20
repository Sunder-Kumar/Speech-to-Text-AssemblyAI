import os
from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv
import spacy

load_dotenv()

app = Flask(__name__)

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
HEADERS = {"authorization": ASSEMBLYAI_API_KEY}

nlp = spacy.load("en_core_web_sm")

def upload_audio(file_path):
    with open(file_path, "rb") as f:
        response = requests.post(
            "https://api.assemblyai.com/v2/upload",
            headers=HEADERS,
            files={"file": f},
        )
    response.raise_for_status()
    return response.json()["upload_url"]

def transcribe_audio(audio_url, language_code, enable_speaker_labels):
    request_payload = {
        "audio_url": audio_url,
        "language_code": language_code,
        "speaker_labels": enable_speaker_labels,
    }

    response = requests.post(
        "https://api.assemblyai.com/v2/transcript",
        headers=HEADERS,
        json=request_payload,
    )
    response.raise_for_status()
    return response.json()

def get_transcription(transcript_id):
    response = requests.get(
        f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
        headers=HEADERS,
    )
    response.raise_for_status()
    return response.json()


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    language_code = request.form.get("language_code", "en")  
    enable_speaker_labels = request.form.get("enable_speaker_labels", "false").lower() == "true"

    audio_file = request.files["file"]
    file_path = f"uploads/{audio_file.filename}"
    os.makedirs("uploads", exist_ok=True)
    audio_file.save(file_path)

    try:
        audio_url = upload_audio(file_path)

        transcription_response = transcribe_audio(audio_url, language_code, enable_speaker_labels)
        transcript_id = transcription_response["id"]

        return jsonify({"transcript_id": transcript_id, "status": "queued"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/transcription/<transcript_id>", methods=["GET"])
def transcription(transcript_id):
    try:
        result = get_transcription(transcript_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
