class SentimentModel:
    def __init__(self):
        # Ce message sera visible dans "docker logs sentiment"
        print("[SentimentModel] Modèle chargé")

    def predict(self, text: str) -> dict:
        text_lower = text.lower()

        positive_words = [
            "bien",
            "super",
            "excellent",
            "parfait",
            "bon",
            "aime",
            "adore",
        ]
        negative_words = [
            "mal",
            "nul",
            "horrible",
            "mauvais",
            "déteste",
            "pire",
        ]

        # Compter les occurrences de mots positifs et négatifs
        pos = sum(1 for word in positive_words if word in text_lower)
        neg = sum(1 for word in negative_words if word in text_lower)

        if pos > neg:
            return {
                "label": "POSITIVE",
                "score": min(round(0.6 + 0.1 * pos, 2), 1.0),
                "text": text,
            }

        if neg > pos:
            return {
                "label": "NEGATIVE",
                "score": min(round(0.6 + 0.1 * neg, 2), 1.0),
                "text": text,
            }

        return {
            "label": "NEUTRAL",
            "score": 0.5,
            "text": text,
        }


def format_label_for_display(label: str) -> str:
    return label
