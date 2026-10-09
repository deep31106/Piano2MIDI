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