
from pathlib import Path
import sys

import mido

# Make the src-layout package importable when running from the project root.
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from piano2midi.evaluation.metrics import (
    evaluate_notes,
    evaluate_note_set,
)

PREDICTIONS_DIR = Path.home() / "Desktop" / "transcriptions testing"
REFERENCE_DIR = PROJECT_ROOT / "data" / "raw" / "maestro"

# Prediction filename -> matching ground-truth MIDI filename.
FILES = [
    "MIDI-UNPROCESSED_01-03_R1_2014_MID--AUDIO_01_R1_2014_wav--1",
    "ORIG-MIDI_01_7_6_13_Group__MID--AUDIO_03_R1_2013_wav--3",
    "ORIG-MIDI_01_7_6_13_Group__MID--AUDIO_04_R1_2013_wav--1",
]

ONSET_TOLERANCE = 0.020  # 20 ms
OFFSET_TOLERANCE = 0.050  # 50 ms


def midi_to_notes(midi_path):
    """Read MIDI note events and convert their times to seconds."""
    midi = mido.MidiFile(midi_path)
    events = []

    for track in midi.tracks:
        tick = 0
        for msg in track:
            tick += msg.time
            events.append((tick, msg))

    def priority(event):
        msg = event[1]
        if msg.type == "set_tempo":
            return 0
        if msg.type == "note_off" or (
            msg.type == "note_on" and msg.velocity == 0
        ):
            return 1
        if msg.type == "note_on":
            return 2
        return 3

    events.sort(key=lambda event: (event[0], priority(event)))

    tempo = 500_000
    previous_tick = 0
    elapsed = 0.0
    active = {}
    notes = []

    for tick, msg in events:
        elapsed += mido.tick2second(
            tick - previous_tick, midi.ticks_per_beat, tempo
        )
        previous_tick = tick

        if msg.type == "set_tempo":
            tempo = msg.tempo

        elif msg.type == "note_on" and msg.velocity > 0:
            key = (msg.channel, msg.note)
            active.setdefault(key, []).append(elapsed)

        elif msg.type == "note_off" or (
            msg.type == "note_on" and msg.velocity == 0
        ):
            key = (msg.channel, msg.note)
            starts = active.get(key, [])

            if starts:
                onset = starts.pop(0)
                notes.append({
                    "pitch": msg.note,
                    "onset": onset,
                    "offset": elapsed,
                })

    return notes


def main():
    print("Piano2MIDI evaluation")
    print(f"Onset tolerance:  {ONSET_TOLERANCE * 1000:.0f} ms")
    print(f"Offset tolerance: {OFFSET_TOLERANCE * 1000:.0f} ms")
    print("=" * 65)

    for basename in FILES:
        prediction_path = PREDICTIONS_DIR / f"{basename}.mid"
        reference_path = REFERENCE_DIR / f"{basename}.midi"

        print(f"\nRecording: {basename}")

        missing = [
            path for path in (prediction_path, reference_path)
            if not path.is_file()
        ]
        if missing:
            for path in missing:
                print(f"  MISSING: {path}")
            continue

        try:
            predictions = midi_to_notes(prediction_path)
            ground_truth = midi_to_notes(reference_path)

            # Pitch + onset matching, ignoring note offsets.
            onset_results = evaluate_note_set(
                ground_truth,
                predictions,
                onset_tolerance=ONSET_TOLERANCE,
            )

            # Strict matching: pitch, onset, and offset.
            strict_results = evaluate_notes(
                ground_truth,
                predictions,
                onset_tolerance=ONSET_TOLERANCE,
                offset_tolerance=OFFSET_TOLERANCE,
            )

            print(f"  Ground-truth notes: {len(ground_truth)}")
            print(f"  Predicted notes:    {len(predictions)}")
            print(
                "  Pitch/onset F1:     "
                f"{onset_results['F1']:.4f} "
                f"(P={onset_results['precision']:.4f}, "
                f"R={onset_results['recall']:.4f})"
            )
            print(
                "  Strict note F1:     "
                f"{strict_results['F1']:.4f} "
                f"(P={strict_results['precision']:.4f}, "
                f"R={strict_results['recall']:.4f})"
            )
            print(
                f"  Onset TP/FP/FN: "
                f"{onset_results['TP']}/"
                f"{onset_results['FP']}/"
                f"{onset_results['FN']}"
            )
            print(
                f"  Strict TP/FP/FN: "
                f"{strict_results['TP']}/"
                f"{strict_results['FP']}/"
                f"{strict_results['FN']}"
            )

        except Exception as exc:
            print(f"  ERROR: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
