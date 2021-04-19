import os
import subprocess

FOLDER = "audio"

os.chdir(FOLDER)

paths = (path for path in os.listdir(".") if path.endswith(".mp3"))
for mp3_file in paths:
    subprocess.call(f'ffmpeg -i "{mp3_file}" -acodec pcm_u8 -ar 48000 "{mp3_file.replace(".mp3", "")}.wav"',
                    shell=True)
    os.remove(mp3_file)
