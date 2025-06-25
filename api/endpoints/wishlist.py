from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session, joinedload
from fastapi.concurrency import run_in_threadpool
from typing import List
from scraper.core import executar_scraping
from db.models import Produto, HistoricoPreco, SessionLocal

# ---------------------------------
# MODELOS DE DADOS (PYDANTIC)
# ---------------------------------

class WishlistPayload(BaseModel):
    url: HttpUrl

class HistoricoPrecoResponse(BaseModel):
    preco: float
    data_extracao: datetime
    class Config:
        from_attributes = True

class ProdutoComHistoricoResponse(BaseModel):
    id: int
    asin: str
    nome: str
    link_produto: HttpUrl
    link_imagem: HttpUrl
    historico_precos: List[HistoricoPrecoResponse] = []
    class Config:
        from_attributes = True

class ProdutoResumoResponse(BaseModel):
    id: int
    asin: str
    nome: str
    link_produto: HttpUrl
    class Config:
        from_attributes = True

# ---------------------------------
# SETUP DO ROUTER E BANCO
# ---------------------------------

router = APIRouter(
    prefix="/api",
    tags=["Wishlist & Products"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------
# ENDPOINTS
# ---------------------------------

@router.post("/scrape-wishlist/")
async def scrape_wishlist(payload: WishlistPayload, db: Session = Depends(get_db)):
    wishlist_url = str(payload.url)
    if "amazon.com" not in wishlist_url:
        raise HTTPException(status_code=400, detail="A URL fornecida não parece ser da Amazon.")
    if "/hz/wishlist/ls/" not in wishlist_url:
        raise HTTPException(status_code=400, detail="A URL não parece ser de uma lista de desejos.")
    try:
        dados_raspados = await run_in_threadpool(executar_scraping, wishlist_url)
        if dados_raspados.get("error_code"):
            error_details = {"WISHLIST_NOT_FOUND": (404, dados_raspados["error"]),"WISHLIST_EMPTY_OR_PRIVATE": (400, dados_raspados["error"])}
            status_code, detail = error_details.get(dados_raspados["error_code"], (500, dados_raspados["error"]))
            raise HTTPException(status_code=status_code, detail=detail)
        
        itens_processados = 0
        for item in dados_raspados.get("itens", []):
            produto_existente = db.query(Produto).filter(Produto.asin == item['asin']).first()
            if not produto_existente:
                produto_existente = Produto(asin=item['asin'], nome=item['nome'], link_produto=item['link'], link_imagem=item['imagem'])
                db.add(produto_existente)
                db.flush()
            if item['preco'] is None:
                continue
            data_extracao_obj = datetime.strptime(item['data_extracao'], '%Y-%m-%d %H:%M:%S')
            novo_historico = HistoricoPreco(produto_id=produto_existente.id, preco=item['preco'], data_extracao=data_extracao_obj)
            db.add(novo_historico)
            itens_processados += 1
        db.commit()
        return {"message": "Scraping concluído com sucesso!", "wishlist_name": dados_raspados.get('nome_da_lista'), "items_processed": itens_processados}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro inesperado na API: {str(e)}")


@router.get("/products/{asin}/history", response_model=ProdutoComHistoricoResponse)
def get_product_history(asin: str, db: Session = Depends(get_db)):
    produto = db.query(Produto).options(joinedload(Produto.historico_precos)).filter(Produto.asin == asin).first()
    if not produto:
        raise HTTPException(status_code=404, detail=f"Produto com ASIN '{asin}' não encontrado.")
    return produto


@router.get("/products/", response_model=List[ProdutoResumoResponse])
def get_all_products(db: Session = Depends(get_db)):
    """
    Lista um resumo de todos os produtos registrados no banco de dados.
    """
    produtos = db.query(Produto).all()
    return produtos