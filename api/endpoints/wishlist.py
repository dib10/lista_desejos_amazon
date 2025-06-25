
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session, joinedload
from fastapi.concurrency import run_in_threadpool
from typing import List, Dict, Any
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
# LÓGICA DE SERVIÇO  
# ---------------------------------

def processar_dados_raspados_no_db(db: Session, dados_raspados: Dict[str, Any]) -> int:
    """
    Processa os dados de uma raspagem, salvando produtos e históricos no banco.
    Retorna a quantidade de itens processados com preço.
    """
    itens_processados = 0
    itens_para_processar = dados_raspados.get("itens", [])

    if not itens_para_processar:
        return 0

    # Mapeia ASINs para produtos existentes para evitar múltiplas queries no loop
    asins = {item['asin'] for item in itens_para_processar}
    produtos_existentes_map = {p.asin: p for p in db.query(Produto).filter(Produto.asin.in_(asins)).all()}

    for item in itens_para_processar:
        produto = produtos_existentes_map.get(item['asin'])

        if not produto:
            produto = Produto(
                asin=item['asin'],
                nome=item['nome'],
                link_produto=item['link'],
                link_imagem=item['imagem']
            )
            db.add(produto)
            db.flush()  

        if item.get('preco') is None:
            continue

        data_extracao_obj = datetime.strptime(item['data_extracao'], '%Y-%m-%d %H:%M:%S')
        novo_historico = HistoricoPreco(
            produto_id=produto.id,
            preco=item['preco'],
            data_extracao=data_extracao_obj
        )
        db.add(novo_historico)
        itens_processados += 1
    
    db.commit()
    return itens_processados


def validar_url_wishlist(url: str):
    """Valida se a URL é de uma wishlist da Amazon."""
    if "amazon.com" not in url or "/hz/wishlist/ls/" not in url:
        raise HTTPException(
            status_code=400, 
            detail="A URL fornecida não parece ser de uma lista de desejos válida da Amazon."
        )

def tratar_erros_scraper(dados_raspados: Dict[str, Any]):
    """Verifica e levanta exceções HTTP para erros conhecidos do scraper."""
    if error_code := dados_raspados.get("error_code"):
        error_details = {
            "WISHLIST_NOT_FOUND": (404, dados_raspados["error"]),
            "WISHLIST_EMPTY_OR_PRIVATE": (400, dados_raspados["error"])
        }
        status_code, detail = error_details.get(error_code, (500, dados_raspados["error"]))
        raise HTTPException(status_code=status_code, detail=detail)


# ---------------------------------
# ENDPOINTS 
# ---------------------------------

@router.post("/scrape-wishlist/")
async def scrape_wishlist(payload: WishlistPayload, db: Session = Depends(get_db)):
    """
    Endpoint para iniciar a raspagem de uma wishlist, salvar os produtos e seu histórico de preço.
    """
    wishlist_url = str(payload.url)
    validar_url_wishlist(wishlist_url)

    try:
        dados_raspados = await run_in_threadpool(executar_scraping, wishlist_url)
        
        tratar_erros_scraper(dados_raspados)

        itens_processados = processar_dados_raspados_no_db(db, dados_raspados)
        
        return {
            "message": "Scraping concluído com sucesso!",
            "wishlist_name": dados_raspados.get('nome_da_lista'),
            "items_processed": itens_processados
        }

    except HTTPException as http_exc:
        raise http_exc 
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ocorreu um erro inesperado na API ao processar a wishlist.")


@router.get("/products/{asin}/history", response_model=ProdutoComHistoricoResponse)
def get_product_history(asin: str, db: Session = Depends(get_db)):
    """Busca um produto pelo seu ASIN e retorna seu histórico de preços."""
    produto = db.query(Produto).options(joinedload(Produto.historico_precos)).filter(Produto.asin == asin).first()
    
    if not produto:
        raise HTTPException(status_code=404, detail=f"Produto com ASIN '{asin}' não encontrado.")
    
    return produto


@router.get("/products/", response_model=List[ProdutoResumoResponse])
def get_all_products(db: Session = Depends(get_db)):
    """Lista um resumo de todos os produtos registrados no banco de dados."""
    produtos = db.query(Produto).all()
    return produtos