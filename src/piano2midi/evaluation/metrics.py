def notes_match(true_note, predicted_note,
    onset_tolerance = 0.05,
    offset_tolerance = 0.05):

    if true_note['pitch']!=predicted_note['pitch']:
        return False

    onset_error = abs(true_note['onset']-predicted_note['onset'])

    if onset_error>onset_tolerance:
        return False

    offset_error = abs(true_note['offset']-predicted_note['offset'])

    if offset_error>offset_tolerance:
        return False

    return True

def evaluate_notes(ground_truth, predictions,
                   onset_tolerance=0.05,
                   offset_tolerance = 0.05):

    matched_true = set()
    matched_pred = set()

    for pred_idx, pred_note in enumerate(predictions):
        for true_idx, true_note in enumerate(ground_truth):

            if true_idx in matched_true:
                continue

            if notes_match(true_note, pred_note, onset_tolerance, offset_tolerance):
                matched_true.add(true_idx)
                matched_pred.add(pred_idx)
                break

    tp = len(matched_pred)
    fp = len(predictions) - tp
    fn = len(ground_truth) - tp
    precision = tp/(tp+fp) if tp+fp else 0.0
    recall = tp/(tp+fn) if tp+fn else 0.0

    f1 = (2*precision*recall/(precision + recall) if precision + recall else 0.0)

    return {
            'TP':tp,
            'FP':fp,
            'FN':fn,
            'precision':precision,
            'recall':recall,
            'F1':f1,
        }


def evaluate_note_set(
    ground_truth,
    predictions,
    onset_tolerance=0.05,
):
    """Evaluate note detection using pitch and onset only.

    A matched note may still have an incorrect offset.
    """
    matched_true = set()
    matched_pred = set()
    matches = []

    for pred_idx, pred_note in enumerate(predictions):
        best_true_idx = None
        best_onset_error = float("inf")

        for true_idx, true_note in enumerate(ground_truth):
            if true_idx in matched_true:
                continue

            if true_note["pitch"] != pred_note["pitch"]:
                continue

            onset_error = abs(
                true_note["onset"] - pred_note["onset"]
            )

            if (
                onset_error <= onset_tolerance
                and onset_error < best_onset_error
            ):
                best_true_idx = true_idx
                best_onset_error = onset_error

        if best_true_idx is not None:
            matched_true.add(best_true_idx)
            matched_pred.add(pred_idx)
            matches.append((best_true_idx, pred_idx))

    tp = len(matched_pred)
    fp = len(predictions) - tp
    fn = len(ground_truth) - tp

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    return {
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "precision": precision,
        "recall": recall,
        "F1": f1,
        "matches": matches,
    }


def evaluate_matched_offsets(
    ground_truth,
    predictions,
    matches,
):
    """Measure offset errors for notes matched by pitch and onset."""
    if not matches:
        return {
            "matched_notes": 0,
            "mean_absolute_offset_error": None,
        }

    errors = [
        abs(
            ground_truth[true_idx]["offset"]
            - predictions[pred_idx]["offset"]
        )
        for true_idx, pred_idx in matches
    ]

    return {
        "matched_notes": len(errors),
        "mean_absolute_offset_error": sum(errors) / len(errors),
    }
