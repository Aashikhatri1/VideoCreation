

# from pytube import YouTube

# def download_youtube_video(url, path):
#     try:
#         # Create YouTube object
#         yt = YouTube(url)

#         # Select the highest resolution stream
#         video_stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()

#         # Check if the stream is available
#         if not video_stream:
#             print("No suitable video stream found")
#             return

#         # Download the video
#         video_stream.download(output_path=path)
#         print(f"Downloaded '{yt.title}' successfully to {path}")

#     except Exception as e:
#         print(f"An error occurred: {e}")

# # Example usage
# youtube_url = "https://youtu.be/gJLVTKhTnog?feature=shared"
# output_path = "InputFiles"  # Assuming this folder already exists

# download_youtube_video(youtube_url, output_path)


from pytube import YouTube
import csv
import os

def download_youtube_video(url, path, filename):
    try:
        # Create YouTube object
        yt = YouTube(url)

        # Select the highest resolution stream
        video_stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()

        # Check if the stream is available
        if not video_stream:
            print("No suitable video stream found")
            return

        # Download the video
        video_stream.download(output_path=path, filename=filename)
        print(f"Downloaded '{yt.title}' successfully to {os.path.join(path, filename)}")

    except Exception as e:
        print(f"An error occurred: {e}")

def download_videos_from_csv(csv_file, output_path):
    with open(csv_file, newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            youtube_url = row['YoutubeVid']
            background_vid = row['BackgroundVid']
            if youtube_url:  # Check if the Youtube URL is not empty
                download_youtube_video(youtube_url, output_path, background_vid)

# Example usage
csv_file_path = "./InputFiles/VideoConfig.csv"  # Path to your CSV file
output_path = "InputFiles"  # Update this to your desired output path

download_videos_from_csv(csv_file_path, output_path)
