from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_health():
    """Vérifie que l'endpoint /health répond avec status 200."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_predict_positive():
    """Vérifie qu'une prédiction retourne la bonne structure de réponse."""
    response = client.post(
        "/predict",
        json={"text": "Ce produit est excellent !"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["label"] in ["POSITIVE", "NEGATIVE", "NEUTRAL"]
    assert 0 <= data["score"] <= 1
    assert data["text"] == "Ce produit est excellent !"


def test_predict_empty_fails():
    """Vérifie que Pydantic rejette un texte vide avec une erreur 422."""
    response = client.post("/predict", json={"text": ""})
    assert response.status_code == 422
