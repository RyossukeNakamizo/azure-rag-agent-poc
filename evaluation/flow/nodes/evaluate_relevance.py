from promptflow.core import tool
@tool
def evaluate_relevance(question: str, answer: str) -> float:
    question_words = set(question.lower().split())
    answer_words = set(answer.lower().split())
    if not question_words: return 0.0
    return min(len(question_words & answer_words) / len(question_words), 1.0)
