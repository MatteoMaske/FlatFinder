def intent_stats(y_true, y_pred):
    """Compute the statistics for the NLU model
    
    Args:
        y_true (list): The ground truth
        y_pred (list): The NLU output
        
    Returns:
        None
    """
    from sklearn.metrics import (
        accuracy_score,
        precision_score,
        recall_score,
        f1_score,
        confusion_matrix,
        classification_report
    )
    import seaborn as sns
    import matplotlib.pyplot as plt

    # Simulated ground truth and predictions (3 intents)
    y_true = []
    y_true.extend(('HOUSE_SEARCH,'*3).split(",")[:-1])
    y_true.extend(('HOUSE_SELECTION,'*3).split(",")[:-1])
    y_true.extend(('ASK_INFO,'*3).split(",")[:-1])
    y_true.extend(('COMPARE_HOUSES,'*3).split(",")[:-1])
    y_true.extend(('OUT_OF_DOMAIN,'*3).split(",")[:-1])

    y_pred = []
    y_pred.extend(('HOUSE_SEARCH,'*2).split(",")[:-1])
    y_pred.append('HOUSE_SELECTION')
    y_pred.extend(('HOUSE_SELECTION,'*3).split(",")[:-1])
    y_pred.extend(('ASK_INFO,'*2).split(",")[:-1])
    y_pred.append('COMPARE_HOUSES')
    y_pred.extend(('OUT_OF_DOMAIN,'*3).split(",")[:-1])
    y_pred.extend(('OUT_OF_DOMAIN,'*3).split(",")[:-1])



    # Accuracy
    accuracy = accuracy_score(y_true, y_pred)
    print(f"Accuracy: {accuracy:.2f}")

    # Macro Precision, Recall, F1
    precision = precision_score(y_true, y_pred, average='macro')
    recall = recall_score(y_true, y_pred, average='macro')
    f1 = f1_score(y_true, y_pred, average='macro')

    print(f"Macro Precision: {precision:.2f}")
    print(f"Macro Recall:    {recall:.2f}")
    print(f"Macro F1-score:  {f1:.2f}")

    # Full classification report (per-intent)
    print("\nClassification Report:")
    print(classification_report(y_true, y_pred))

    # Confusion Matrix
    labels = sorted(set(y_true))
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    plt.figure(figsize=(12, 10))
    sns.heatmap(cm, annot=True, fmt='d', xticklabels=labels, yticklabels=labels, cmap='Blues', cbar=False)
    plt.xlabel("Predicted", fontsize=12)
    plt.xticks(rotation=15, ha='right', fontsize=10)
    plt.ylabel("True", fontsize=12)
    plt.yticks(fontsize=10)
    plt.title("Confusion Matrix", fontsize=14)
    plt.savefig("test/house_agency/intent_confusion_matrix.png", bbox_inches='tight')
    plt.show()

# TODO: Handle none values in the slots
def slots_stats(true_slots, pred_slots, fuzz_th=80, bert_th=0.85):
    """Compute the combined match score using fuzzy matching and BERTScore"""
    from sklearn.metrics import precision_score, recall_score, f1_score
    from bert_score import BERTScorer
    import fuzzywuzzy.fuzz as fuzz

    # Compute fuzzy decisions
    fuzz_decisions = [
        fuzz.ratio(t.lower(), p.lower()) >= fuzz_th
        for t, p in zip(true_slots, pred_slots)
    ]
    # Compute BERTScore once
    scorer = BERTScorer(lang="en", rescale_with_baseline=True)
    _, _, bert_f1 = scorer.score(pred_slots, true_slots)

    # TODO: Test this approach
    y_true = true_slots
    y_pred = [
        int(fz or (bf1 >= bert_th)) # remove this and put the gt value in order to compute meaningful precision and recall
        for fz, bf1 in zip(fuzz_decisions, bert_f1.tolist())
    ]

    # Compute precision, recall, and F1 score
    precision = precision_score(y_true, y_pred),
    recall = recall_score(y_true, y_pred),
    f1 = f1_score(y_true, y_pred)

    print(f"Slots Precision: {precision:.2f}")
    print(f"Slots Recall:    {recall:.2f}")
    print(f"Slots F1-score:  {f1:.2f}")

    return (
        precision_score(y_true, y_pred),
        recall_score(y_true, y_pred),
        f1_score(y_true, y_pred)
    )


intent_stats([], [])
slots_stats([], [])