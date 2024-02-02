# Flow: first crop the videos and then merge them, then add audio and then caption according to timestamp.
# resolution changes done 
# Transcription ending words missing problem fixed

import pandas as pd
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip, TextClip, CompositeVideoClip
import os
import certifi
import ssl
from deepgram import Deepgram
from PIL import Image
import numpy as np
from datetime import datetime

code_started = datetime.now()
print(code_started)

# Use certifi's CA bundle
ssl_context = ssl.create_default_context(cafile=certifi.where())
ssl._create_default_https_context = lambda: ssl_context


config_file = "./InputFiles/VideoConfig.csv"
df = pd.read_csv(config_file)
# Assuming only the first row contains the audio file name
audio_file = df['AudioFile'][0]  
audio_path = os.path.join("InputFiles", audio_file) 


# Standard resolution to which all videos will be resized
STANDARD_WIDTH = 1920
STANDARD_HEIGHT = 1080

def resize_frame(frame, new_width=1920, new_height=1080):
    """Resize a single video frame."""
    pil_image = Image.fromarray(frame)
    resized_pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    return np.array(resized_pil_image)

def resize_video_clip(video_clip, new_width=1920, new_height=1080):
    """Resize a video clip to the specified dimensions."""
    return video_clip.fl_image(lambda frame: resize_frame(frame, new_width, new_height))

# Function to crop and merge videos
def crop_and_merge_videos(config_file):
    df = pd.read_csv(config_file)
    clips = []

    for index, row in df.iterrows():
        video_file = os.path.join("InputFiles", row['BackgroundVid'])  # Updated path
        start_time = row['CropVideoFrom']
        end_time = row['CropVideoTill']
        # output_dir = row['OutputDire']
        output_dir = "./VideoOutput"

        if not os.path.exists(video_file):
            print(f"Video file {video_file} not found.")
            continue

        clip = VideoFileClip(video_file).subclip(start_time, end_time)
        clip = resize_video_clip(clip, 1920, 1080)

        clips.append(clip)

    final_clip = concatenate_videoclips(clips)
    output_file = os.path.join(output_dir, "merged_video.mp4")  # Updated output file path

    final_clip.write_videofile(output_file, codec='libx264', audio_codec='aac')
    for clip in clips:
        clip.close()
    final_clip.close()

    return output_file

def get_transcription():
    
    if not os.path.exists(audio_path):
        print(f"Audio file {audio_path} not found.")
        return

    # Deepgram setup
    dg_key = '967c5ce3f89d5cbb8c74107737ba36b9e1a5ba20' # Replace with your actual Deepgram API key
    dg = Deepgram(dg_key)
    MIMETYPE = 'mp3'
    options = {
        "punctuate": True,
        "model": 'general',
        "tier": 'enhanced'
    }

    # Read and process audio file for transcription
    with open(audio_path, "rb") as f:
        source = {"buffer": f, "mimetype": 'audio/' + MIMETYPE}
        res = dg.transcription.sync_prerecorded(source, options)

    # Extract words and create transcriptions
    words = res['results']['channels'][0]['alternatives'][0]['words']
    transcriptions = []
    # for i in range(0, len(words), 4):
    #     group = words[i:i + 4]
    #     if len(group) == 4:
    #         text = " ".join(word['word'] for word in group)
    #         start_time = round(group[0]['start'], 2)
    #         end_time = round(group[-1]['end'], 2)
    #         duration = end_time - start_time
    #         transcriptions.append({"timestamp": start_time, "duration": duration, "text": text})

    for i in range(0, len(words), 4):
        group = words[i:i + 4]
        text = " ".join(word['word'] for word in group)
        start_time = round(group[0]['start'], 2)
        end_time = round(group[-1]['end'], 2)
        duration = end_time - start_time
        transcriptions.append({"timestamp": start_time, "duration": duration, "text": text})
    #print(transcriptions)
    return transcriptions


def convert_time_to_seconds(time_str):
    """Converts a time string in HH:MM:SS format to total seconds as float."""
    hours, minutes, seconds = map(float, time_str.split(':'))
    return hours * 3600 + minutes * 60 + seconds

# Updated main function to include transcriptions based on specified times
def main(merged_video_file, config_file, transcriptions):
    df = pd.read_csv(config_file)
    video_clip = VideoFileClip(merged_video_file)

    # Set audio to video clip
    audio_clip = AudioFileClip(audio_path)
    video_clip = video_clip.set_audio(audio_clip)

    # Generate text clips based on transcriptions for each configuration row
    composite_clips = []
    for index, row in df.iterrows():

        # Convert start and end times to float
        start_audio_time = convert_time_to_seconds(row['CropAudioFrom'])
        end_audio_time = convert_time_to_seconds(row['CropAudioTill'])
        font_size = int(row['FontSize'])  # Ensure this is also correctly typed
        font_color = row['FontColour']
        align = row['FontPosition']

        # Filter transcriptions for current segment
        
        segment_transcriptions = [
            t for t in transcriptions
            if t['timestamp'] >= start_audio_time and t['timestamp'] < end_audio_time
        ]
        #print('segment_transcriptions', segment_transcriptions)
        # Create text clips for each transcription in the segment
        for transcription in segment_transcriptions:
            #print('transcription', transcription)
            text_clip = create_text_clip(
                transcription, video_clip.size, font_size, font_color, align
            ) #.set_start(transcription['timestamp']).set_duration(transcription['duration'])
            composite_clips.append(text_clip)

    # Create final composite clip
    final_clip = CompositeVideoClip([video_clip] + composite_clips)
    output_dir = "./VideoOutput"
    output_video_path = os.path.join(output_dir, "output_video_with_captions.mp4")
    final_clip.write_videofile(output_video_path, codec='libx264', audio_codec='aac', fps=24)

    # Cleanup
    video_clip.close()
    audio_clip.close()
    for clip in composite_clips[1:]:
        clip.close()


def create_text_clip(transcription, size, font_size, font_color, align):
    # Create a TextClip for each transcription
    return TextClip(
        txt=transcription["text"], 
        fontsize=font_size, 
        color=font_color, 
        align=align,
        size=size
    ).set_start(transcription["timestamp"]).set_duration(transcription["duration"])

transcriptions = get_transcription()
merged_video_file = crop_and_merge_videos(config_file)
main(merged_video_file, config_file, transcriptions)


code_finished = datetime.now()
time_taken = code_finished - code_started
print(code_finished)
print(time_taken)
