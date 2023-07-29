from django.http import HttpResponse
from moviepy.editor import VideoFileClip
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
import json
import re
import speech_recognition as sr
from pydub import AudioSegment
import requests
import assemblyai as aai
from googletrans import Translator
import whisper


@csrf_protect
@csrf_exempt
def postVideo(request):
    # extractAudio(videoPath, videoPath[0:len(videoPath)-4]+".mp3")
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Extracting videopath and lang from JSON
            videoPath=re.sub(r'\\\\', r'\\',data["videoPath"])
            lang=data["lang"]

            # Extracting audio
            outputPath=videoPath[0:len(videoPath)-4]+".mp3"
            extractAudio(videoPath,outputPath)
            print(outputPath)

            outputWavPath=videoPath[0:len(videoPath)-4]+".wav"
            inputWavPath=outputPath

            wavConvert(inputWavPath,outputWavPath)            

            # Extracting text
            text=speechToText(outputWavPath)

            hindiTextFile=translate_to_hindi(text,outputWavPath)

            # Add voice in 11labs
            voice_id=addVoice(request,outputWavPath)

            # Giving text to 11 labs
            addText11(request,hindiTextFile,voice_id)
            return JsonResponse({'videoPath':videoPath,'lang':lang})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON format'})
    else:
        return JsonResponse({'success': False, 'message': 'Only POST requests are allowed'})

def extractAudio(videoPath, outputPath):
    try:

        videoClip = VideoFileClip(videoPath)

        # Extract the audio from the video
        audioClip = videoClip.audio

        # Save the extracted audio to the specified output path
        audioClip.write_audiofile(outputPath,codec='mp3')

        # Close the clips
        audioClip.close()
        videoClip.close()

        print("Audio extraction successful.")
    except Exception as e:
        print("Error extracting audio:", str(e))

def wavConvert(inputPath, outputPath):

    print(inputPath,outputPath)
    # Load the MP3 file using pydub
    audio = AudioSegment.from_mp3(inputPath)

    # Export the audio as a WAV file
    audio.export(outputPath, format='wav')

def translate_to_hindi(text,filePath):
    translator = Translator()
    translated_text = translator.translate(text, src='en', dest='hi')
    # saving text in a file
    filePath=filePath[0:-4]+"hindi.txt"
    with open(filePath, 'w',encoding='utf-8') as file:
        file.write(translated_text.text)
    return filePath
    # return translated_text.text

def speechToText(filePath):
    model = whisper.load_model("base.en")
    result = model.transcribe(filePath)
    filePath=filePath[0:-4]+".txt"
    with open(filePath, 'w') as file:
        file.write(result['text'])
    return result['text']

# 11 labs functions
def addVoice(request,wavPath):

    url = "https://api.elevenlabs.io/v1/voices/add"

    headers = {
    "Accept": "application/json",
    "xi-api-key": "fc3395a73afe62ac77c4099589cc5e85"
    }

    data = {
        'name': 'morgan',
        'labels': '{"accent": "American"}',
        'description': 'Voice description'
    }

    files = [
        ('files', (wavPath, open(wavPath, 'rb'), 'audio/mpeg')),
    ]

    response = requests.post(url, headers=headers, data=data, files=files)
    print(response.text)
    if response.status_code == 200:
        # Parse the response JSON and access the 'voice_id' attribute
        response_data = response.json()
        voice_id = response_data.get('voice_id')
        print("Voice ID:", voice_id)
        return voice_id
    else:
        print("Error: Request failed with status code", response.status_code)
        return None

def addText11(request,filePathHindi,voice_id):
    CHUNK_SIZE = 1024
    url = "https://api.elevenlabs.io/v1/text-to-speech/"+voice_id+"/stream"

    headers = {
    "Accept": "audio/mpeg",
    "Content-Type": "application/json",
    "xi-api-key": "fc3395a73afe62ac77c4099589cc5e85"
    }

    with open(filePathHindi,'r',encoding="utf-8") as file:
        contents=file.read()

    data = {
    "text": contents,
    "model_id": "eleven_multilingual_v1",
    "voice_settings": {
        "stability": 1,
        "similarity_boost": 1
    }
    }
    print(data)
    response = requests.post(url, json=data, headers=headers)
    hindiAudio=filePathHindi[0:-4]+".mp3"
    with open(hindiAudio, 'wb') as f:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            if chunk:
                f.write(chunk)