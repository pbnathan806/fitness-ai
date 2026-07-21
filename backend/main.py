from fastapi import FastAPI

app = FastAPI(title="Fitness AI Platform")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"status": "ok"}
