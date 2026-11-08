# Hold:
```
curl -X POST http://127.0.0.1:5000/alert-start \
  -H "Content-Type: application/json" \
  -d '{
    "task": "hold",
    "description": "your description here"
  }'


curl -X GET http://127.0.0.1:5000/alert-get
```