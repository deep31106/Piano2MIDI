# Piano2MIDI

**A local, offline-first piano audio-to-MIDI converter for Windows.**

Piano2MIDI converts piano recordings into MIDI files using the pretrained [Transkun](https://github.com/) transcription engine. It provides a graphical interface and command-line interface, with support for batch processing and CPU/GPU inference.

The project focuses on accurate note pitches, onset timing, durations, and polyphonic transcription.

## Features

- **Graphical interface:** Dark-themed GUI, drag-and-drop, file browsing, transcription queue, and output-folder selection.
- **Command-line interface:** Transcribe individual files, multiple files, or entire directories.
- **Audio and video inputs:** Extract audio from supported video files using FFmpeg.
- **Online media:** Download supported YouTube and Instagram media using `yt-dlp`.
- **CPU/GPU inference:** Select CPU or CUDA, depending on your installation and hardware.
- **Local processing:** Transcribe local files offline after installing the required software and model files.
- **MIDI output:** Generate standard `.mid` files for compatible music software.

Online downloads require an internet connection and depend on source accessibility and `yt-dlp` compatibility.

## Architecture

```text
Audio / Video / Online URL
           |
           v
     Piano2MIDI GUI or CLI
           |
           v
      Input preparation
      (FFmpeg / yt-dlp)
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

Piano2MIDI wraps the pretrained Transkun transcription engine rather than training its own neural transcription model.

## Requirements

- Windows
- Python 3.12 for the main application environment
- Python 3.11 for the separate Transkun environment
- FFmpeg installed and available on `PATH`
- A compatible NVIDIA GPU and CUDA-enabled PyTorch installation for GPU inference; CPU inference is also supported with a compatible installation

The application and Transkun use separate Python environments to isolate their dependencies.

## Installation

Run the following commands from the project root in PowerShell.

### 1. Set up the main application environment

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
```

This installs Piano2MIDI and its declared application dependencies.

### 2. Install development dependencies

For tests, notebooks, and development utilities:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Install optional online support

Online URL downloads require `yt-dlp`.

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[online]"
```

You can skip this step if you only intend to transcribe local files.

### 4. Set up Transkun

Transkun runs in a separate Python 3.11 environment.

Create the environment and install the packages declared in `requirements-transkun.txt`:

```powershell
py -3.11 -m venv .venv-transkun311
.\.venv-transkun311\Scripts\python.exe -m pip install --upgrade pip
.\.venv-transkun311\Scripts\python.exe -m pip install -r requirements-transkun.txt
```

The Transkun requirements file contains:

- `ncls==0.0.68`
- `transkun==2.0.1`
- `setuptools<81`

#### Install PyTorch and TorchAudio

PyTorch and TorchAudio must be installed separately in the Transkun environment. The appropriate build depends on your hardware and CUDA compatibility.

For the project's current CUDA 12.8 development setup:

```powershell
.\.venv-transkun311\Scripts\python.exe -m pip install torch==2.9.1 torchaudio==2.9.1 --index-url https://download.pytorch.org/whl/cu128
```

For a CPU-only system, install a compatible CPU build of PyTorch and TorchAudio instead.

GPU inference requires a compatible NVIDIA driver and CUDA-enabled PyTorch installation. These commands document the project's current development setup, not a guarantee that the same build is suitable for every machine.

### 5. Install FFmpeg

FFmpeg is an external program, not a Python package.

Install FFmpeg for Windows and add its executable directory to your system `PATH`.

Verify it:

```powershell
ffmpeg -version
```

FFmpeg is required for video audio extraction and online downloads. Local audio transcription does not need FFmpeg for input preparation.

## Usage

### Launch the GUI

From the project root:

```powershell
.\.venv\Scripts\python.exe -m piano2midi.gui
```

Alternatively, double-click `launch_piano2midi.bat` in the project root after setting up both environments.

The GUI supports file selection, drag-and-drop, queued transcription jobs, output-folder selection, online URLs, and CPU/CUDA selection.

### Transcribe one audio file

```powershell
.\.venv\Scripts\piano2midi.exe "C:\Path\To\song.mp3" --transkun-executable ".\.venv-transkun311\Scripts\transkun.exe"
```

### Transcribe a video

```powershell
.\.venv\Scripts\piano2midi.exe "C:\Path\To\performance.mp4" --transkun-executable ".\.venv-transkun311\Scripts\transkun.exe"
```

Video inputs require FFmpeg.

### Transcribe an online URL

```powershell
.\.venv\Scripts\piano2midi.exe --url "https://www.youtube.com/watch?v=VIDEO_ID" --transkun-executable ".\.venv-transkun311\Scripts\transkun.exe"
```

Online transcription requires internet access, `yt-dlp`, and FFmpeg. The source must be accessible to the downloader.

### Choose an output directory

```powershell
.\.venv\Scripts\piano2midi.exe "C:\Path\To\song.mp3" --output-dir "D:\MIDI" --transkun-executable ".\.venv-transkun311\Scripts\transkun.exe"
```

### Transcribe multiple files

```powershell
.\.venv\Scripts\piano2midi.exe "C:\Path\To\song1.mp3" "C:\Path\To\song2.wav" --output-dir "D:\MIDI" --transkun-executable ".\.venv-transkun311\Scripts\transkun.exe"
```

### Transcribe a directory

```powershell
.\.venv\Scripts\piano2midi.exe --input-dir "C:\Path\To\Recordings" --output-dir "D:\MIDI" --transkun-executable ".\.venv-transkun311\Scripts\transkun.exe"
```

Include subdirectories using `--recursive`:

```powershell
.\.venv\Scripts\piano2midi.exe --input-dir "C:\Path\To\Recordings" --recursive --output-dir "D:\MIDI" --transkun-executable ".\.venv-transkun311\Scripts\transkun.exe"
```

### Select CPU or CUDA

CUDA is the default:

```powershell
.\.venv\Scripts\piano2midi.exe "song.mp3" --device cuda --transkun-executable ".\.venv-transkun311\Scripts\transkun.exe"
```

Use CPU inference instead:

```powershell
.\.venv\Scripts\piano2midi.exe "song.mp3" --device cpu --transkun-executable ".\.venv-transkun311\Scripts\transkun.exe"
```

CPU inference may be slower, depending on the recording and hardware.

### Overwrite existing MIDI files

Existing output files are skipped by default. Use `--overwrite` to replace them:

```powershell
.\.venv\Scripts\piano2midi.exe "song.mp3" --overwrite --transkun-executable ".\.venv-transkun311\Scripts\transkun.exe"
```

For the complete list of options:

```powershell
.\.venv\Scripts\piano2midi.exe --help
```

## Supported formats

| Input type | Extensions |
|---|---|
| Audio | `.wav`, `.mp3`, `.flac`, `.ogg` |
| Video | `.mp4`, `.mov` |

Online formats depend on what `yt-dlp` can download and convert successfully.

## Evaluation

Piano2MIDI was evaluated against matching audio and MIDI recordings from the [MAESTRO dataset](https://magenta.tensorflow.org/datasets/maestro).

Three selected recordings were transcribed through the GUI and evaluated against their corresponding reference MIDI files using the project's evaluation utilities.

### Results

| Recording | Pitch/onset F1 | Strict note F1 |
|---|---:|---:|
| MAESTRO 2014 recording | 99.85% | 94.47% |
| MAESTRO 2013 — segment 3 | 98.88% | 88.88% |
| MAESTRO 2013 — segment 1 | 99.74% | 96.27% |
| **Unweighted mean** | **99.49%** | **93.20%** |

### Evaluation methodology

- **Pitch/onset F1:** A predicted note matches when its pitch is correct and its onset is within 20 ms of the reference onset. Note offsets are ignored for this metric.
- **Strict note F1:** A predicted note must have the correct pitch, onset within 20 ms, and offset within 50 ms.
- Precision, recall, F1, true positives, false positives, and false negatives are calculated by the project's evaluation utilities.
- The reported mean gives each recording equal weight.

These results are measurements on three selected recordings, not a comprehensive benchmark or a guarantee of performance on arbitrary recordings. Results can vary with audio quality, instrument sound, reverberation, and recording conditions.

### Reproducing the evaluation

The local `results.py` helper compares the generated MIDI files in the Desktop `transcriptions testing` folder against reference MIDI files under `data/raw/maestro`.

Keep the original reference MIDI files and predictions in their expected locations when running the script. The reference recordings are evaluation assets and should not be committed to the repository.

## Development and tests

Run the automated test suite from the project root:

```powershell
$env:PYTHONPATH = "$PWD\src"
.\.venv-transkun311\Scripts\python.exe -m pytest -q
Remove-Item Env:PYTHONPATH
```

The current regression suite contains 18 tests.

The repository also contains evaluation utilities, notebooks, and benchmark scripts. Some experiments require local datasets, recordings, or model files that are not distributed with the source code.

## Troubleshooting

### Transkun executable not found

Confirm that the separate Python 3.11 environment is installed and that this file exists:

```text
.venv-transkun311\Scripts\transkun.exe
```

If needed, provide the executable path using `--transkun-executable`.

### FFmpeg not found

Run:

```powershell
ffmpeg -version
```

If PowerShell cannot find it, check the installation and system `PATH`, then restart the terminal.

### Online downloads fail

- Confirm `yt-dlp` is installed in the main environment.
- Confirm FFmpeg is available on `PATH`.
- Check that the URL is supported and accessible.
- Some sources may restrict access or require authentication.

### CUDA errors

Check that the NVIDIA driver, PyTorch/TorchAudio build, and Transkun environment are compatible. If necessary, try CPU inference.

### Existing output is skipped

Use `--overwrite` if you want to regenerate an existing output file.

## Repository hygiene

Do not commit virtual environments, model weights, large datasets, personal recordings, or generated transcription outputs unless they are intentionally included as project assets.

The MAESTRO recordings used for evaluation are not bundled with this repository. MAESTRO is distributed under the **CC BY-NC-SA 4.0** license; consult the dataset's license and attribution requirements before redistributing any of its materials.

## Project status

- [x] Transkun integration
- [x] CLI for local and online inputs
- [x] GUI with drag-and-drop and a transcription queue
- [x] CPU/GPU device selection
- [x] Video audio extraction
- [x] Optional online URL support
- [x] MIDI evaluation utilities
- [x] Automated regression tests
- [x] Evaluation on three selected MAESTRO recordings
- [ ] Final clean-environment verification
- [ ] Standalone Windows distribution

Piano2MIDI currently relies on a separately installed Transkun environment. The `launch_piano2midi.bat` file provides a convenient local launcher; a self-contained Windows distribution is a possible future improvement.
