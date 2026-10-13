# Piano2MIDI

A local, offline-first piano audio-to-MIDI converter built in Python.

Piano2MIDI uses a pretrained transcription model to convert piano recordings into MIDI files, with the goal of preserving note pitches, onsets, durations, and polyphony as accurately as possible.

## Current Status

- [x] Audio fundamentals and preprocessing experiments
- [x] MIDI event handling and evaluation metrics
- [x] DSP-based transcription experiments
- [x] Transkun pretrained-model inference on Windows GPU
- [x] Python wrapper around the Transkun CLI
- [x] Automated tests for wrapper behaviour
- [x] Command-line interface for single-file and batch transcription
- [x] Configurable CPU/GPU inference
- [x] Real-world transcription tests on multiple piano recordings
- [ ] Convenient global Windows command and launcher
- [ ] MP4/video audio extraction
- [ ] Standalone Windows distribution
- [ ] Optional piano-roll viewer

Transcription quality has been promising across several real-world recordings. Accuracy may vary with the recording, audio quality, and musical content.

## Architecture

```text
Audio file
    ↓
Piano2MIDI CLI
    ↓
Transkun backend wrapper
    ↓
Transkun transcription engine
    ↓
MIDI output
```

Piano2MIDI delegates neural transcription to Transkun rather than implementing or training its own transcription model.

## Requirements

- Windows
- Python 3.11 or 3.12 for the main project
- Python 3.11 for the current Transkun environment
- FFmpeg available on `PATH` for the current Transkun setup
- A compatible NVIDIA GPU and CUDA-enabled PyTorch installation for GPU inference, or CPU inference as an alternative

The project currently uses two separate Python environments to keep the main project dependencies separate from Transkun's dependencies.

## Installation

### 1. Create the main project environment

From the project root in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

### 2. Install development dependencies

For notebooks, experiments, and development:

```powershell
python -m pip install -r requirements.txt
python -m pip install pytest
```

### 3. Set up Transkun

Create its separate Python 3.11 environment:

```powershell
py -3.11 -m venv .venv-transkun311
.\.venv-transkun311\Scripts\Activate.ps1
python -m pip install "ncls==0.0.68"
python -m pip install "transkun==2.0.1"
python -m pip install "setuptools<81"
python -m pip install torch==2.9.1 torchaudio==2.9.1 --index-url https://download.pytorch.org/whl/cu128
```

The PyTorch installation command above targets CUDA 12.8-compatible wheels. GPU inference requires a compatible NVIDIA driver.

Install FFmpeg separately and ensure that it is available on `PATH`.

**Note:** These instructions describe the current development setup. A one-step installer and self-contained Windows distribution are future work.

## Usage

Activate the main `.venv` and run the CLI from the project root.

### Transcribe one audio file

```powershell
piano2midi "C:\Path\To\song.mp3" --transkun-executable ".\.venv-transkun311\Scripts\transkun.exe"
```

By default, the MIDI file is written to the `transcriptions` directory using the input filename with a `.mid` extension.

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

GPU inference is the default:

```powershell
piano2midi "song.mp3" --device cuda --transkun-executable ".\.venv-transkun311\Scripts\transkun.exe"
```

Use CPU inference instead:

```powershell
piano2midi "song.mp3" --device cpu --transkun-executable ".\.venv-transkun311\Scripts\transkun.exe"
```

### Overwrite an existing MIDI file

Existing outputs are skipped by default. To replace them:

```powershell
piano2midi "song.mp3" --overwrite --transkun-executable ".\.venv-transkun311\Scripts\transkun.exe"
```

### View available options

```powershell
piano2midi --help
```

Supported input formats are WAV, MP3, FLAC, and OGG. MP4/video extraction is not implemented yet.

## Evaluation

The project includes MIDI evaluation utilities for:

- Strict note matching by pitch, onset, and offset
- Note detection matching by pitch and onset
- Offset-error analysis for matched notes
- Precision, recall, F1 score, false positives, and false negatives

The evaluation work is exploratory and uses reference MIDI files where available. Results from individual recordings should not be interpreted as a universal measure of transcription accuracy.

## Development and Tests

Install the project in editable mode:

```powershell
python -m pip install -e .
```

Run the Transkun backend tests:

```powershell
python -m pytest tests/test_transkun_backend.py -v
```

The Phase 6 evaluation notebook and benchmark script contain additional experiments. Some benchmark scripts rely on local test files and datasets that are not included in the repository.

## Repository Hygiene

Local virtual environments, model weights, raw and processed datasets, and personal transcription test files are excluded from version control. Keep large audio files, generated MIDI outputs, and downloaded model artifacts out of Git unless they are intentionally added as project assets.

## Roadmap

1. Make the CLI convenient to launch from any Windows terminal without manual environment activation.
2. Improve output-path handling and usability.
3. Add MP4 audio extraction using FFmpeg.
4. Investigate a standalone Windows distribution that includes the required runtime, Transkun dependencies, and model files.
5. Consider an optional flowing-note piano-roll viewer after the core transcription workflow is stable.

Transcription quality remains the primary goal. Further model-quality changes will be driven by significant, reproducible issues found during real-world use.