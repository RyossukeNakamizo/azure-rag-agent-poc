from promptflow.core import tool
@tool
def evaluate_coherence(answer: str) -> float:
    wc = len(answer.split())
    return 0.3 if wc < 10 else 0.7 if wc < 50 else 0.9 if wc < 200 else 0.6
