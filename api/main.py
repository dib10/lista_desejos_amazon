from fastapi import FastAPI
from api.endpoints import wishlist 

app = FastAPI(title="Amazon Wishlist Scraper API")

app.include_router(wishlist.router)

@app.get("/")
def read_root():
    return {"message": "API do Scraper no ar!"}
