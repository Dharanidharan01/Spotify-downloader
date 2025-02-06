import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp
import zipfile
import uuid

class SpotifyPlaylistDownloader:
    def __init__(self, client_id, client_secret):
        client_credentials_manager = SpotifyClientCredentials(
            client_id=client_id, 
            client_secret=client_secret
        )
        self.sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    def get_playlist_tracks(self, playlist_url):
        # Extract playlist ID from URL
        playlist_id = playlist_url.split('/')[-1].split('?')[0]
        
        # Fetch playlist tracks
        results = self.sp.playlist_tracks(playlist_id)
        tracks = results['items']
        
        # Handle pagination if playlist has more than 100 tracks
        while results['next']:
            results = self.sp.next(results)
            tracks.extend(results['items'])
        
        # Prepare track details
        track_details = [
            {
                'name': track['track']['name'],
                'artist': track['track']['artists'][0]['name']
            } 
            for track in tracks if track['track']
        ]
        
        return track_details

    def download_tracks(self, tracks, max_tracks=100):
        # Limit number of tracks to prevent excessive downloads
        tracks = tracks[:max_tracks]
        
        # Create temporary download directory
        download_dir = f'downloads_{uuid.uuid4()}'
        os.makedirs(download_dir, exist_ok=True)

        # YouTube Music downloader configuration
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
            'nooverwrites': True,
            'no_color': True,
            'quiet': True
        }

        # Download tracks
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            for track in tracks:
                search_query = f"{track['name']} {track['artist']} audio"
                try:
                    ydl.download([f"ytsearch1:{search_query}"])
                except Exception as e:
                    print(f"Could not download {search_query}: {e}")

        # Create ZIP file
        zip_filename = f'{download_dir}.zip'
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(download_dir):
                for file in files:
                    zipf.write(os.path.join(root, file), file)

        # Clean up temporary directory
        os.rmdir(download_dir)

        return zip_filename

def main():
    # Get credentials from environment variables or input
    CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID') or input("Enter Spotify Client ID: ")
    CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET') or input("Enter Spotify Client Secret: ")

    # User input
    playlist_url = input("Enter Spotify Playlist URL: ")

    # Initialize downloader
    downloader = SpotifyPlaylistDownloader(CLIENT_ID, CLIENT_SECRET)

    # Get tracks
    tracks = downloader.get_playlist_tracks(playlist_url)

    # Download and ZIP tracks
    zip_file = downloader.download_tracks(tracks)
    print(f"Playlist downloaded successfully: {zip_file}")

if __name__ == "__main__":
    main()