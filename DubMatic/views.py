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
from pydub import AudioSegment
from pydub.playback import play
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
import subprocess
from moviepy.editor import VideoFileClip, AudioFileClip
from moviepy.audio.fx import audio_loop
import os

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
            audioMp3=videoPath[0:len(videoPath)-4]+".mp3"
            extractAudio(videoPath,audioMp3)
            # print(outputPath)

            outputWavPath=videoPath[0:len(videoPath)-4]+".wav"
            inputWavPath=audioMp3

            wavConvert(inputWavPath,outputWavPath)   
            print("audio extracted")

            # Extracting text
            text=speechToText(outputWavPath)
            print("text extracted")

            translatedTextFile=translateTextToTargetLang(text,outputWavPath,lang)
            print("text converted")

            # # Add voice in 11labs
            voice_id=addVoice(request,outputWavPath)
            print("voice added to 11 labs")

            # # Giving text to 11 labs
            translatedAudioPath=addText11(request,translatedTextFile,voice_id)
            print("audio retrieved from 11 labs")

            # addaudio to video
            translatedVideoPath=translatedAudioPath[0:-4]+".mp4"
            replace_audio_in_video(videoPath,translatedAudioPath,translatedVideoPath) 
            print("audio added to video")
            os.remove(audioMp3) 
            os.remove(outputWavPath) 
            os.remove(translatedTextFile) 
            os.remove(translatedAudioPath) 


            
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

        # print("Audio extraction successful.")
    except Exception as e:
        print("Error extracting audio:", str(e))

def wavConvert(inputPath, outputPath):

    # print(inputPath,outputPath)
    # Load the MP3 file using pydub
    audio = AudioSegment.from_mp3(inputPath)
    # Export the audio as a WAV file
    audio.export(outputPath, format='wav')
    

def translateTextToTargetLang(text,filePath,target_lang):
    translator = Translator()
    translated_text = translator.translate(text, src='en', dest=target_lang)
    # saving text in a file
    filePath=filePath[0:-4]+"translate.txt"
    with open(filePath, 'w',encoding='utf-8') as file:
        file.write(translated_text.text)
    return filePath
    # return translated_text.text

def speechToText(filePath):
    model = whisper.load_model("base.en")
    result = model.transcribe(filePath)
    # filePath=filePath[0:-4]+".txt"
    # with open(filePath, 'w') as file:
    #     file.write(result['text'])
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
        'labels': '{"accent": "Indian"}',
        'description': 'Voice description'
    }

    files = [
        ('files', (wavPath, open(wavPath, 'rb'), 'audio/mpeg')),
    ]

    response = requests.post(url, headers=headers, data=data, files=files)
    # print(response.text)
    if response.status_code == 200:
        # Parse the response JSON and access the 'voice_id' attribute
        response_data = response.json()
        voice_id = response_data.get('voice_id')
        # print("Voice ID:", voice_id)
        return voice_id
    else:
        print("Error: Request failed with status code", response.status_code)
        return None

def addText11(request,filePathHindi,voice_id):
    CHUNK_SIZE = 2048
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
    # print(data)
    response = requests.post(url, json=data, headers=headers)
    translated_audio=filePathHindi[0:-4]+".mp3"
    with open(translated_audio, 'wb') as f:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            if chunk:
                f.write(chunk)
    return translated_audio

def replace_audio_in_video(video_path, audio_path, output_path):
    video_clip = VideoFileClip(video_path)
    audio_clip = AudioFileClip(audio_path)
    video_with_new_audio = video_clip.set_audio(audio_clip)
    video_with_new_audio.write_videofile(output_path, codec="libx264", audio_codec="aac") 