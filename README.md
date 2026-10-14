# Piano2MIDI

**A local, offline-first piano audio-to-MIDI converter for Windows.**

Piano2MIDI converts piano recordings into MIDI files using the pretrained [Transkun](https://github.com/) transcription engine. It provides a graphical interface and a command-line interface, with support for batch processing and configurable CPU/GPU inference.

The goal is to produce useful MIDI transcriptions that preserve note pitches, timing, durations, and polyphony.

## Features

- **Graphical interface:** Dark-themed GUI with drag-and-drop, file browsing, a transcription queue, and output-folder selection.
- **Command-line interface:** Transcribe individual files, multiple files, or entire directories.
- **Audio and video inputs:** Extract audio from supported video files using FFmpeg.
- **Online media:** Download audio from supported YouTube and Instagram URLs using `yt-dlp`.
- **CPU/GPU inference:** Choose CPU or CUDA inference, depending on your hardware and installation.
- **Local processing:** Local files can be transcribed without an internet connection once the required software and model files are installed.
- **MIDI output:** Generate `.mid` files for use in a digital audio workstation or MIDI-compatible software.

Online downloads require an internet connection. Availability of online media depends on the source, access restrictions, and `yt-dlp` compatibility.

## Architecture

```text
Audio / Video / Online URL
            |
            v
     Piano2MIDI GUI or CLI
            |
            v
   Input preparation
   (FFmpeg / yt-dlp when needed)
            |
            v
    Transkun backend wrapper
            |
            v
      Transkun model
            |
            v
         MIDI file
```

Piano2MIDI uses Transkun for neural transcription rather than training its own transcription model.

## Requirements

- Windows
- Python 3.12 for the main application environment
- Python 3.11 for the separate Transkun environment
- FFmpeg installed and available on `PATH` for video extraction and online downloads
- A compatible NVIDIA GPU and CUDA-enabled PyTorch installation for GPU inference, or CPU inference as an alternative

The application and Transkun use separate Python environments to keep their dependencies isolated.

## Installation

Run the following commands from the project root in PowerShell.

### 1. Create the main environment

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

This installs Piano2MIDI and its main application dependencies.

### 2. Install development dependencies

For notebooks, experiments, and testing:

```powershell
python -m pip install -r requirements.txt
```

### 3. Install optional online support

To enable URL downloads:

```powershell
python -m pip install -e ".[online]"
```

This installs `yt-dlp`. Online downloads also require FFmpeg.

### 4. Set up Transkun

Create the separate Python 3.11 environment:

```powershell
py -3.11 -m venv .venv-transkun311
.\.venv-transkun311\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install "ncls==0.0.68"
python -m pip install "transkun==2.0.1"
python -m pip install "setuptools<81"
```

Install PyTorch and TorchAudio using a compatible build for your machine.

For the current CUDA 12.8 development setup:

```powershell
python -m pip install torch==2.9.1 torchaudio==2.9.1 --index-url https://download.pytorch.org/whl/cu128
```

GPU inference requires a compatible NVIDIA driver. For CPU-only systems, install a compatible CPU build of PyTorch and TorchAudio instead.

**Important:** These commands document the current development setup. PyTorch and Transkun compatibility can depend on the Python version, operating system, hardware, and package releases.

### 5. Install FFmpeg

FFmpeg is an external program, not a Python package, so it is not installed through `requirements.txt`.

Install FFmpeg for Windows and add its executable directory to your system `PATH`.

Verify the installation:

```powershell
ffmpeg -version
```

Video extraction and online audio downloads require FFmpeg. Local audio-file transcription does not need FFmpeg for input preparation.

## Usage

Activate the main environment before using the CLI or GUI:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Launch the graphical interface

From the project root:

```powershell
python -m piano2midi.gui
```

The GUI supports:

- Dragging and dropping supported media files
- Browsing for local files
- Adding online media URLs
- Selecting an output directory
- Choosing CUDA or CPU inference
- Processing queued jobs and cancelling a batch

### Transcribe one audio file

```powershell
piano2midi "C:\Path\To\song.mp3" --transkun-executable ".\.venv-transkun311\Scripts\transkun.exe"
```

### Transcribe a video

```powershell
piano2midi "C:\Path\To\performance.mp4" --transkun-executable ".\.venv-transkun311\Scripts\transkun.exe"
```

FFmpeg is required for video audio extraction.

### Transcribe an online URL

```powershell
piano2midi --url "https://www.youtube.com/watch?v=VIDEO_ID" --transkun-executable ".\.venv-transkun311\Scripts\transkun.exe"
```

Online URL support requires `yt-dlp`, FFmpeg, and internet access. The URL must be supported by the application and accessible to the downloader.

### Choose an output directory

```powershell
piano2midi "C:\Path\To\song.mp3" --output-dir "D:\MIDI" --transkun-executable ".\.venv-transkun311\Scripts\transkun.exe"
```

### Transcribe multiple files

```powershell
piano2midi "C:\Path\To\song1.mp3" "C:\Path\To\song2.wav" --output-dir "D:\MIDI" --transkun-executable ".\.venv-transkun311\Scripts\transkun.exe"
```

### Transcribe a directory

```powershell
piano2midi --input-dir "C:\Path\To\Recordings" --output-dir "D:\MIDI" --transkun-executable ".\.venv-transkun311\Scripts\transkun.exe"
```

Include subdirectories with `--recursive`:

```powershell
piano2midi --input-dir "C:\Path\To\Recordings" --recursive --output-dir "D:\MIDI" --transkun-executable ".\.venv-transkun311\Scripts\transkun.exe"
```

### Select the inference device

CUDA is the default:

```powershell
piano2midi "song.mp3" --device cuda --transkun-executable ".\.venv-transkun311\Scripts\transkun.exe"
```

Use CPU inference instead:

```powershell
piano2midi "song.mp3" --device cpu --transkun-executable ".\.venv-transkun311\Scripts\transkun.exe"
```

CPU inference may be slower, depending on the recording and machine.

### Overwrite existing MIDI files

Existing output files are skipped by default. To replace them:

```powershell
piano2midi "song.mp3" --overwrite --transkun-executable ".\.venv-transkun311\Scripts\transkun.exe"
```

### View available options

```powershell
piano2midi --help
```

## Supported formats

The CLI currently accepts the following input extensions:

| Type | Extensions |
|---|---|
| Audio | `.wav`, `.mp3`, `.flac`, `.ogg` |
| Video | `.mp4`, `.mov` |

Video inputs require FFmpeg to extract their audio before transcription.

Online media formats depend on what `yt-dlp` can download and convert successfully.

## Output

By default, MIDI files are saved in the `transcriptions` directory.

For local inputs, the output filename is based on the input filename, with a `.mid` extension. Use `--output-dir` to select another destination.

The output is a standard MIDI file that can be opened in compatible music software for listening, editing, and further arrangement.

## Troubleshooting

### Transkun executable not found

Confirm that Transkun is installed in the separate Python 3.11 environment. You can explicitly provide its executable path:

```powershell
piano2midi "song.mp3" --transkun-executable ".\.venv-transkun311\Scripts\transkun.exe"
```

### FFmpeg not found

Run:

```powershell
ffmpeg -version
```

If PowerShell cannot find the command, check the FFmpeg installation and your system `PATH`. Restart the terminal after modifying `PATH`.

### Online downloads fail

- Confirm that the main environment has `yt-dlp` installed.
- Confirm that FFmpeg is available.
- Check that the URL is supported and accessible.
- Some videos may require authentication or may be unavailable to the downloader.

### CUDA errors

Confirm that the NVIDIA driver, CUDA-compatible PyTorch installation, and Transkun environment are compatible. If necessary, try `--device cpu`.

### Existing output is skipped

Piano2MIDI avoids replacing existing MIDI files by default. Add `--overwrite` if you want to regenerate an output.

## Development and Tests

Install the project in editable mode:

```powershell
python -m pip install -e .
```

Run the automated test suite from the project root:

```powershell
$env:PYTHONPATH = "$PWD\src"
.\.venv-transkun311\Scripts\python.exe -m pytest -q
Remove-Item Env:PYTHONPATH
```

The current regression suite contains 18 tests.

The repository also contains notebooks, evaluation utilities, and benchmark scripts. Some experiments require local datasets, recordings, or model files that are not distributed with the source code.

## Repository Hygiene

Local virtual environments, model weights, datasets, recordings, generated MIDI files, Python caches, and temporary files should remain outside version control unless intentionally included as project assets.

Check `.gitignore` before committing changes, particularly when adding generated outputs or local test data.

## Current Status

- [x] Transkun integration
- [x] CLI for local and online inputs
- [x] GUI with drag-and-drop and a transcription queue
- [x] CPU/GPU device selection
- [x] Video audio extraction
- [x] Optional online URL support
- [x] MIDI evaluation utilities
- [x] Automated regression tests
- [ ] Final clean-environment verification
- [ ] Standalone Windows distribution for sharing

Transcription quality is the primary deliverable. The project currently relies on a separately installed Transkun environment; a self-contained distribution is planned as a later step.