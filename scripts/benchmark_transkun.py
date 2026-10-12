
from pathlib import Path

import mido

from piano2midi.evaluation.metrics import evaluate_notes


def midi_to_notes(midi_path):
    """Convert MIDI note events to pitch/onset/offset dictionaries in seconds."""
    midi = mido.MidiFile(midi_path)

    # Merge tracks so events are processed in chronological tick order.
    events = []
    for track in midi.tracks:
        absolute_tick = 0
        for message in track:
            absolute_tick += message.time
            events.append((absolute_tick, message))

    events.sort(key=lambda item: item[0])

    tempo = 500_000  # MIDI default: 120 BPM
    previous_tick = 0
    elapsed_seconds = 0.0
    active_notes = {}
    notes = []

    for tick, message in events:
        elapsed_seconds += (
            (tick - previous_tick)
            * tempo
            / 1_000_000
            / midi.ticks_per_beat
        )
        previous_tick = tick

        if message.type == "set_tempo":
            tempo = message.tempo

        elif message.type == "note_on" and message.velocity > 0:
            key = (message.channel, message.note)
            active_notes.setdefault(key, []).append(elapsed_seconds)

        elif message.type == "note_off" or (
            message.type == "note_on" and message.velocity == 0
        ):
            key = (message.channel, message.note)
            starts = active_notes.get(key, [])
            if starts:
                onset = starts.pop(0)
                notes.append(
                    {
                        "pitch": message.note,
                        "onset": onset,
                        "offset": elapsed_seconds,
                    }
                )

    return notes


def main():
    project_root = Path(__file__).resolve().parents[1]
    test_dir = Path.home() / "projects" / "piano2midi-test"

    prediction_path = test_dir / "piano_sample_20s.mid"
    reference_path = Path(
        "/mnt/c/Users/Deep/Desktop/Deep/Piano2MIDI/"
        "piano2midi/data/raw/maestro/piano_sample.midi"
    )

    if not prediction_path.exists():
        raise FileNotFoundError(prediction_path)
    if not reference_path.exists():
        raise FileNotFoundError(reference_path)

    predictions = midi_to_notes(prediction_path)
    ground_truth = midi_to_notes(reference_path)

    # Keep reference notes whose onsets fall inside the 20-second excerpt.
    ground_truth = [note for note in ground_truth if note["onset"] < 20.0]
    predictions = [note for note in predictions if note["onset"] < 20.0]

    results = evaluate_notes(
        ground_truth,
        predictions,
        onset_tolerance=0.05,
        offset_tolerance=0.05,
    )

    print(f"Reference notes: {len(ground_truth)}")
    print(f"Predicted notes: {len(predictions)}")
    for name, value in results.items():
        if isinstance(value, float):
            print(f"{name}: {value:.4f}")
        else:
            print(f"{name}: {value}")


if __name__ == "__main__":
    main()