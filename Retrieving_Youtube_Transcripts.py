import csv
import os
from youtube_transcript_api import YouTubeTranscriptApi as yta

# Function to extract transcript and save it to CSV
def youtube_transcripts(links, file_path):
    try:
        # Check if the file exists and if it needs a header
        file_exists = os.path.isfile(file_path)
        with open(file_path, 'a', newline='', encoding='utf-8') as csvfile:
            csvwriter = csv.writer(csvfile)
            # Write the header if the file does not exist
            if not file_exists:
                csvwriter.writerow(['YouTube Link', 'Language', 'Transcript'])
            for link in links:
                # Extract the video ID from the YouTube link
                vid_id = link.split('/')[-1].split('?')[0]
                transcripts = yta.list_transcripts(vid_id)
                for transcript in transcripts:
                    try:
                        data = transcript.fetch()  # Fetch the transcript data
                        # Process the data to extract and clean the text
                        final_data = ' '.join([val['text'] for val in data]).replace('\n', ' ').strip()
                        # Write the data with language
                        csvwriter.writerow([link, transcript.language, final_data])
                    except Exception as e:
                        print(
                            f"An error occurred while fetching the transcript for language {transcript.language}: {e}")
        print(f"Transcripts saved to '{file_path}'.")
    except Exception as e:
        print(f"An error occurred: {e}")

# List of YouTube links
links = [
    'https://youtu.be/c76pzDJQGWM?si=WCND9KvtO7JfM5q3', #replace with actual YouTube URL
]
# Path to save the CSV file
file_path = r'C:\Users\HP\OneDrive\Desktop\transcripts\BP.csv'  # Use raw string to handle backslashes
youtube_transcripts(links, file_path)
