from django.http import HttpResponse
from moviepy.editor import VideoFileClip
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
import json
import re
import speech_recognition as sr
from pydub import AudioSegment


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
            text=transcribe_audio(outputWavPath)
            print(text)

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



# Extracting text
def transcribe_audio(audio_file_path):
    # Initialize the speech recognizer
    recognizer = sr.Recognizer()

    try:
        # Load the audio file
        with sr.AudioFile(audio_file_path) as audio_file:
            # Record the audio from the file
            audio = recognizer.record(audio_file)

            # Use Google Web Speech API to transcribe the audio
            text = recognizer.recognize_google(audio)

            # saving text in a file
            filePath=audio_file_path[0:-4]+".txt"
            with open(filePath, 'w') as file:
                file.write(text)

            return text
    except sr.UnknownValueError:
        print("Google Web Speech API could not understand the audio.")
    except sr.RequestError as e:
        print(f"Could not request results from Google Web Speech API; {e}")

    return None
