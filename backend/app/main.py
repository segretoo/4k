from fastapi import FastAPI

app = FastAPI(title="4K - 낯선 사람이 보는 내 아이")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
