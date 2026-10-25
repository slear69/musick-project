
# Ado Music Player

A desktop music player built with Python and CustomTkinter. It plays audio files from a local music folder, shows artwork, supports search, playback controls, and includes a vinyl-style animated disc while a song is playing.

## Features

- Play MP3, WAV, FLAC, OGG, and M4A files
- Search songs by title or artist
- Add music from any folder on your computer
- Auto-load songs from the local music directory
- Display embedded album art or generated cover art
- Seek bar for playback position
- Vinyl-style rotating disc animation
- Lightweight windowed desktop UI

## Project Structure

- `main_gui.py` - Main application window and playback logic
- `vinyl_disk.py` - Vinyl animation component
- `music/` - Folder where music is stored and managed
- `ROSE.png` and `ado.png` - UI decorative assets

## Requirements

This project is designed for Windows.

- Python 3.10 or newer
- `customtkinter`
- `pywinstyles`
- `python-vlc`
- `Pillow`
- `mutagen`

## Installation

1. Open a terminal in the project folder.
2. Install the dependencies:

```bash
pip install customtkinter pywinstyles python-vlc pillow mutagen
```

3. Make sure `vlc` is installed on your system. The Python package `python-vlc` usually works with a local VLC installation.

## Run the App

```bash
python main_gui.py
```

The app will create a `music` folder next to the script if it does not exist yet. Put your audio files there or use the Add Music button inside the app.

## Usage

- Click Add Music to add songs from your computer
- Search for songs using the search field
- Use play, pause, and next controls in the playback bar
- Drag the seek bar to move through the track
- Open the music folder from the app to manage files manually

## Notes

- This app is built mainly for local desktop playback and not a streaming service.
- Artwork is pulled from embedded metadata when available, otherwise it generates a color-based fallback cover.
- The Windows-only `pywinstyles` and `os.startfile` usage are part of the current UI behavior.

## License

This project does not currently include a license file. If you plan to share or distribute it publicly, add a license that matches your intended usage.
