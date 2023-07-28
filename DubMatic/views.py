from django.http import HttpResponse
from moviepy.editor import VideoFileClip

def postVideo(request,videoPath):
    extractAudio(videoPath, videoPath[0:len(videoPath)-4]+".mp3")
    return HttpResponse(f"User Input: {videoPath}")



def extractAudio(videoPath, outputPath):
    try:

        # Load the video file
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


