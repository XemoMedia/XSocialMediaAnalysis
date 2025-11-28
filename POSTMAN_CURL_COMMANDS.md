# Postman cURL Command – Sentiment Analysis

Use the following Postman-generated cURL snippet to call `POST /api/v1/sentiment/analyze` with both comment and reply IDs.

```bash
curl --location 'http://localhost:8000/api/v1/sentiment/analyze' \
  --header 'Content-Type: application/json' \
  --data '{
    "commentIds": [
      "17869867290466511",
      "18112050916589661",
      "17989212311864011",
      "18063369632163573"
    ],
    "repliedIds": [
      "17869867290466511"
    ]
  }'
```

> Tip for Windows CMD: replace each `\` line continuation with `^` and escape quotes like `\"value\"`.