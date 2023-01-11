import json

from typing import List, Dict, Union

import ffmpeg

def read_video(video: str) -> "VideoData":
    # Use ffmpeg to read the video data
    return ffmpeg.input(video)

def read_vtt(vtt: str) -> List[Dict[str, Union[int, str]]]:
    # Read the VTT file as a list of dictionaries
    with open(vtt, "r") as f:
        return json.load(f)

def select_video_portion(video_data: "VideoData", start: int, end: int) -> "VideoData":
    # Use ffmpeg to select the portion of the video between start and end (inclusive)
    return video_data.trim(start=start, end=end)

def warp_video(video_data: "VideoData", audio: str) -> "VideoData":
    # Use ffmpeg to warp the video to match the audio
    return video_data.filter("apad", duration=get_audio_length(audio)).filter("atempo", tempo=2.0)

def replace_audio(video_data: "VideoData", audio: str) -> "VideoData":
    # Use ffmpeg to replace the audio in the video with the TTS audio
    return video_data.audio.filter("aecho", 0.8, 0.9, 1000, 0.3).audio.filter("atempo", tempo=2.0)

def get_audio_length(audio: str) -> int:
    # Use ffmpeg to get the length of the audio file in seconds
    return int(ffmpeg.probe(audio)["format"]["duration"])

def write_vtt(vtt_data: List[Dict[str, Union[int, str]]]) -> None:
    # Write the VTT data to a file
    with open("output.vtt", "w") as f:
        json.dump(vtt_data, f)

def concatenate_videos(videos: List["VideoData"]) -> "VideoData":
    # Use ffmpeg to concatenate the videos
    return ffmpeg.concat(*videos, v=1, a=1)

def process_video(video: str, vtt: str, tts: List[str]) -> "VideoData":
    # Check that the number of VTT entries and TTS audios are the same
    if len(vtt) != len(tts):
        raise ValueError("Number of VTT entries and TTS audios must be the same")
    
    # Read the video and VTT file
    video_data = read_video(video)
    vtt_data = read_vtt(vtt)
    
    # Initialize output video data and VTT data
    output_video_data = []
    output_vtt_data = []
    
    # Iterate through the VTT data
    for i, entry in enumerate(vtt_data):
        # Select the video portion corresponding to the VTT entry
        video_portion = select_video_portion(video_data, entry["start"], entry["end"])
        
        # Warp the video portion to match the TTS audio
        video_portion = warp_video(video_portion, tts[i])
        
        # Replace the audio in the video portion with the TTS audio
        video_portion = replace_audio(video_portion, tts[i])
        
        # Append the video portion to the output video data
        output_video_data.append(video_portion)
        
        # Append the VTT entry to the output VTT data
        output_vtt_data.append(entry)
        
        # If there is a gap between this VTT entry and the next one, fill it with silence
        if i < len(vtt_data) - 1:
            gap_start = entry["end"]
            gap_end = vtt_data[i+1]["start"]
            gap_duration = gap_end - gap_start
            silence = generate_silence(gap_duration)
            output_video_data.append(silence)
    
    # Concatenate the output video data
    output_video = concatenate_videos(output_video_data)
    
    # Write the output VTT data
    write_vtt(output_vtt_data)
    
    return output_video

def process_video_with_tts(video: str, vtt: str, tts: List[str]) -> None:
    # Process the video with the TTS audio
    output_video = process_video(video, vtt, tts)
    
    # Write the output video to a file
    output_video.output("output.mp4").run()

# Example usage:
video = "input.mp4"
vtt = "input.vtt"
tts = ["tts1.mp3", "tts2.mp3", "tts3.mp3"]
process_video_with_tts(video, vtt, tts)
