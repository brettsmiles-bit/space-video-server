from moviepy.editor import ImageClip, AudioFileClip

# Replace these with your own files
audio_path = audio_path = r"c:\Users\kakim\Downloads\file_example_WAV_1MG.wav"
image_path = r"C:\Users\kakim\OneDrive\Desktop\istockphoto-1262409453-1024x1024.jpg"

try:
    audio = AudioFileClip(audio_path)
    clip = ImageClip(image_path, duration=audio.duration)
    clip = clip.set_audio(audio)

    clip.write_videofile("test_output.mp4", fps=24)

    print("✅ MoviePy works! Video saved as test_output.mp4")

except Exception as e:
    print("❌ Error:", e)
