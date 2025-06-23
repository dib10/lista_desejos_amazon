from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, HttpUrl
from scraper.core import executar_scraping

# Modelo Pydantic para validação automática da URL de entrada
class WishlistPayload(BaseModel):
    url: HttpUrl

router = APIRouter(
    prefix="/api",
    tags=["Wishlist"]
)

@router.post("/scrape-wishlist/")
async def scrape_wishlist(payload: WishlistPayload):
    wishlist_url = str(payload.url)

    if "amazon.com" not in wishlist_url:
        raise HTTPException(status_code=400, detail="A URL fornecida não parece ser da Amazon.")

    if "/hz/wishlist/ls/" not in wishlist_url:
        raise HTTPException(
            status_code=400, 
            detail="A URL não parece ser de uma lista de desejos da Amazon. Verifique se ela contém '/hz/wishlist/ls/'."
        )

    try:
        # Chama a função de scraping, que pode retornar dados ou um dicionário de erro
        dados_raspados = await run_in_threadpool(executar_scraping, wishlist_url)

        #  erro específico: lista não encontrada
        if dados_raspados.get("error_code") == "WISHLIST_NOT_FOUND":
            raise HTTPException(status_code=404, detail=dados_raspados["error"])

        #  erro específico: lista vazia ou privada 
        if dados_raspados.get("error_code") == "WISHLIST_EMPTY_OR_PRIVATE":
            raise HTTPException(status_code=400, detail=dados_raspados["error"])

        if dados_raspados.get("error"):
             raise HTTPException(status_code=500, detail=dados_raspados["error"])
        
        return dados_raspados
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro inesperado na API: {str(e)}")