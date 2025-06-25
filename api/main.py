from fastapi import FastAPI
from contextlib import asynccontextmanager
from db.models import Base, engine 
from api.endpoints import wishlist 


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("INFO:     Aplicação iniciando...")
    Base.metadata.create_all(bind=engine)
    print("INFO:     Tabelas do banco de dados verificadas/criadas com sucesso.")
    
    yield 
    
    print("INFO:     Aplicação encerrando.")


app = FastAPI(
    title="Amazon Wishlist Scraper API",
    lifespan=lifespan
)

app.include_router(wishlist.router)


@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API de Scraper da Amazon!"}