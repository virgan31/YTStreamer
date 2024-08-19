from yt_dlp import YoutubeDL
from youtubesearchpython import VideosSearch
from tqdm import tqdm
import os
import tempfile
from pydub import AudioSegment
from pydub.playback import play
import threading
import time

TMP_FOLDER = os.path.join(os.getcwd(), 'tmp')

def search_youtube(query, max_results=5):
    search = VideosSearch(query, limit=max_results)
    results = search.result()['result']
    
    print("\nSearch Results:")
    for index, video in enumerate(results, start=1):
        print(f"{index}. {video['title']} (Duration: {video['duration']})")
        print(f"   Link: {video['link']}\n")
    
    return results

def download_audio(video_url, download_path="."):
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
            'progress_hooks': [progress_hook],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
            print("Download completed!")
            
            # Return the path of the downloaded MP3 file
            info_dict = ydl.extract_info(video_url, download=False)
            mp3_filename = ydl.prepare_filename(info_dict).rsplit('.', 1)[0] + '.mp3'
            return mp3_filename
            
    except Exception as e:
        print(f"Error: {e}")
        return None

def progress_hook(d):
    if d['status'] == 'downloading':
        if not progress_hook.pbar:
            total = d.get('total_bytes', 0)
            progress_hook.pbar = tqdm(total=total, unit='B', unit_scale=True, desc="Downloading")
        
        progress_hook.pbar.update(d['downloaded_bytes'] - progress_hook.pbar.n)
    
    elif d['status'] == 'finished':
        if progress_hook.pbar:
            progress_hook.pbar.close()
        print("Done downloading, now converting...")
progress_hook.pbar = None

def convert_to_wav(mp3_file):
    # Convert MP3 to WAV using pydub
    audio = AudioSegment.from_mp3(mp3_file)
    wav_file = mp3_file.rsplit('.', 1)[0] + '.wav'
    audio.export(wav_file, format="wav")
    return wav_file

def play_audio_with_time_tracking(file_path):
    # Play the audio and track time
    def time_tracker(duration_ms):
        elapsed_time = 0
        while elapsed_time < duration_ms:
            minutes, seconds = divmod(elapsed_time // 1000, 60)
            print(f"\rElapsed Time: {minutes:02}:{seconds:02}", end="")
            time.sleep(1)
            elapsed_time += 1000  # Increment by 1 second
        print()  # New line after playback

    # Load the audio file
    audio = AudioSegment.from_file(file_path)
    duration_ms = len(audio)  # Duration in milliseconds
    
    # Start time tracking in a separate thread
    tracker_thread = threading.Thread(target=time_tracker, args=(duration_ms,))
    tracker_thread.start()
    
    # Play the audio using pydub
    try:
        play(audio)
    except Exception as e:
        print(f"Playback error: {e}")
    
    # Wait for the time tracking thread to finish
    tracker_thread.join()
    
    print("Playback finished.")

def main():
    # Ensure the /tmp directory exists
    if not os.path.exists(TMP_FOLDER):
        os.makedirs(TMP_FOLDER)
    
    query = input("Enter search query: ")
    search_results = search_youtube(query)
    
    try:
        choice = int(input("Enter the number of the video you want to download: "))
        if 1 <= choice <= len(search_results):
            selected_video = search_results[choice - 1]
            print(f"\nSelected: {selected_video['title']}")
            
            print(f"Downloading audio to {TMP_FOLDER}...")
            mp3_file = download_audio(selected_video['link'], TMP_FOLDER)
            
            if mp3_file:
                # Convert MP3 to WAV
                wav_file = convert_to_wav(mp3_file)
                
                # Play the WAV file with time tracking
                play_audio_with_time_tracking(wav_file)

                # Remove the MP3 and WAV files after playback
                os.remove(mp3_file)
                os.remove(wav_file)
                print("Playback finished and temporary files deleted.")
        else:
            print("Invalid choice.")
    except ValueError:
        print("Please enter a valid number.")

if __name__ == "__main__":
    main()
