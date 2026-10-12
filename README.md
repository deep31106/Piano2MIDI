# Piano2MIDI

A local, offline-first piano audio-to-MIDI converter built in Python.

The goal is to convert piano recordings into MIDI files while preserving note pitches, onsets, durations, and polyphony as accurately as possible.

## Current status

- [x] Audio fundamentals and preprocessing experiments
- [x] MIDI event handling and evaluation metrics
- [x] DSP-based transcription baseline
- [x] Transkun pretrained-model inference on Windows GPU
- [x] Python wrapper around the Transkun CLI
- [x] Focused automated tests for wrapper behaviour
- [ ] Complete `piano2midi input.mp3` command
- [ ] Improve transcription quality
- [ ] Optional piano-roll viewer

## Architecture

Audio input → preprocessing → Transkun inference → MIDI output

Transkun is a pretrained transcription model. Piano2MIDI wraps its command-line interface rather than reimplementing the neural network.

## Development environments

The main project uses Python 3.12. Transkun currently runs in a separate Python 3.11 virtual environment because its `ncls` dependency has a compatible prebuilt Windows wheel for that version.

From the project root in PowerShell:

```powershell
py -3.11 -m venv .venv-transkun311
.\.venv-transkun311\Scripts\Activate.ps1
python -m pip install "ncls==0.0.68"
python -m pip install "transkun==2.0.1"
python -m pip install "setuptools<81"
python -m pip install torch==2.9.1 torchaudio==2.9.1 --index-url https://download.pytorch.org/whl/cu128
```

FFmpeg must also be installed and available on `PATH`.

## Running the wrapper

Install the project into the active Python environment:

```powershell
python -m pip install -e .
```

Example:

```powershell
python -c "from piano2midi.transcription.transkun_backend import transcribe; print(transcribe(r'data/processed/piano_sample_20s.wav', r'data/processed/output.mid', device='cuda'))"
```

The wrapper validates the input file and format, invokes Transkun, reports execution failures, and checks that a non-empty output file was produced.

## Tests

Install pytest in the active environment and run:

```powershell
python -m pip install pytest
python -m pytest tests/test_transkun_backend.py -v
```

## Limitations

- The full user-facing CLI is not yet complete.
- Transcription quality has not yet been systematically improved.
- GPU inference requires a compatible NVIDIA driver and CUDA-enabled PyTorch installation.
- The current wrapper accepts WAV, MP3, FLAC, and OGG inputs; video extraction and the final user-facing workflow are still planned.
