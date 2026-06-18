# SentimentAI

API REST FastAPI pour analyser un texte et retourner un sentiment : `POSITIVE`, `NEGATIVE` ou `NEUTRAL`.

## Commandes utiles

```bash
make build
make run
make test
make stop
```

## Tester l'API

```bash
curl http://localhost:8080/health

curl -X POST http://localhost:8080/predict \
  -H "Content-Type: application/json" \
  -d '{"text":"Ce produit est excellent !"}'
```
