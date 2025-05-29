from fastapi import FastAPI
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/api/v1/health")
    print(f"Response status code: {response.status_code}")
    print(f"Response body: {response.json()}")

if __name__ == "__main__":
    test_health() 