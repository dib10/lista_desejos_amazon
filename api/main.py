# api/main.py
from fastapi import FastAPI
from api.endpoints import wishlist  # Importe o módulo do endpoint

app = FastAPI(title="Amazon Wishlist Scraper API")

# Inclua o router do nosso endpoint no app principal
app.include_router(wishlist.router, prefix="/api", tags=["Wishlist"])

@app.get("/")
def read_root():
    return {"message": "API do Scraper no ar!"}