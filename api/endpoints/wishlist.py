
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session, joinedload
from fastapi.concurrency import run_in_threadpool
from typing import List, Dict, Any
from scraper.core import executar_scraping
from db.models import Produto, HistoricoPreco, Wishlist, SessionLocal
from sqlalchemy.orm import Session, joinedload, selectinload




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

class WishlistResponse(BaseModel):
    id: int
    nome_wishlist: str
    url: HttpUrl
    class Config:
        from_attributes = True

class WishlistCreate(BaseModel):
    nome_wishlist: str
    url: HttpUrl

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

def processar_dados_raspados_no_db(db: Session, dados_raspados: Dict[str, Any], wishlist_id: int) -> int:
    """
    Processa os dados de uma raspagem, salvando produtos e históricos no banco, associando-os a uma wishlist.
    """
    itens_processados = 0
    itens_para_processar = dados_raspados.get("itens", [])

    if not itens_para_processar:
        return 0

    # Mapeia ASINs para produtos existentes para evitar múltiplas queries no loop
    asins = {item['asin'] for item in itens_para_processar}
    produtos_existentes_map = {p.asin: p for p in db.query(Produto).filter(Produto.wishlist_id == wishlist_id, Produto.asin.in_(asins)).all()}

    for item in itens_para_processar:
        produto = produtos_existentes_map.get(item['asin'])

        if not produto:
            produto = Produto(
                asin=item['asin'],
                nome=item['nome'],
                link_produto=item['link'],
                link_imagem=item['imagem'],
                wishlist_id=wishlist_id
            )
            db.add(produto)
            db.flush()  

        if item.get('preco') is None:
            continue

        data_extracao_obj = datetime.strptime(item['data_extracao'], '%Y-%m-%d %H:%M:%S')
        novo_historico = HistoricoPreco(
            produto_id=produto.id,
            preco=item['preco'],
            data_extracao=data_extracao_obj,
            wishlist_id=wishlist_id
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
@router.post("/wishlists/", response_model=WishlistResponse, status_code=201, summary="Registrar uma Nova Wishlist (Robusto)")
async def create_wishlist(wishlist_payload: WishlistCreate, db: Session = Depends(get_db)): 
    """
    Registra uma nova wishlist, validando sua acessibilidade antes de salvar.
    """
    wishlist_url = str(wishlist_payload.url)

    validar_url_wishlist(wishlist_url)

    db_wishlist = db.query(Wishlist).filter(Wishlist.url == wishlist_url).first()
    if db_wishlist:
        raise HTTPException(status_code=400, detail="Uma wishlist com esta URL já está registrada.")
    
    try:
        print(f"INFO: Validando acessibilidade da wishlist: {wishlist_url}")
        dados_raspados = await run_in_threadpool(executar_scraping, wishlist_url)
        
        tratar_erros_scraper(dados_raspados)
        
        if not dados_raspados.get("itens"):
            raise HTTPException(status_code=400, detail="A wishlist parece estar vazia ou é privada.")

    except HTTPException as http_exc:
        raise http_exc 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Não foi possível validar a wishlist. Erro: {e}")
    
    nova_wishlist = Wishlist(
        url=wishlist_url,
        nome_wishlist=wishlist_payload.nome_wishlist 
    )
    db.add(nova_wishlist)
    db.commit()
    db.refresh(nova_wishlist)
    
    return nova_wishlist

@router.post("/wishlists/{wishlist_id}/scrape", summary="HU-07: Disparar Atualização de uma Wishlist")
async def scrape_existing_wishlist(wishlist_id: int, db: Session = Depends(get_db)):
    """
    Inicia uma nova varredura de preços para uma wishlist já registrada.
    """
    wishlist = db.query(Wishlist).filter(Wishlist.id == wishlist_id).first()
    if not wishlist:
        raise HTTPException(status_code=404, detail="Wishlist não encontrada.")

    try:
        dados_raspados = await run_in_threadpool(executar_scraping, wishlist.url)
        tratar_erros_scraper(dados_raspados)

        itens_processados = processar_dados_raspados_no_db(
            db=db, 
            dados_raspados=dados_raspados, 
            wishlist_id=wishlist_id
        )

        return {
            "message": f"Scraping da wishlist '{wishlist.nome_wishlist}' concluído!",
            "items_processed": itens_processados
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro inesperado ao processar a wishlist: {e}")

@router.get("/wishlists/{wishlist_id}/products", response_model = List[ProdutoResumoResponse],summary="Listar Produtos de uma Wishlist")
def get_products_from_wishlist(wishlist_id: int, db: Session = Depends(get_db)):
    """
    Retorna uma lista resumida de produtos de uma wishlist específica.
    """
    wishlist = db.query(Wishlist).filter(Wishlist.id == wishlist_id).first()
    if not wishlist:
        raise HTTPException(status_code=404, detail="Wishlist não encontrada.")
    return db.query(Produto).filter(Produto.wishlist_id == wishlist_id).all()

@router.get("/wishlists/{wishlist_id}/products/{asin}/history", response_model=ProdutoComHistoricoResponse, summary="Consultar Histórico de Produto na Wishlist")
def get_product_history_in_wishlist(
    wishlist_id: int, 
    asin: str, 
    db: Session = Depends(get_db)
):
    """
    Retorna o histórico de preços de um produto específico em uma wishlist.
    """
    produto = db.query(Produto).options(
        selectinload(Produto.historico_precos)
    ).filter(
        Produto.wishlist_id == wishlist_id, 
        Produto.asin == asin
    ).first()
    
    if not produto:
        raise HTTPException(status_code=404, detail=f"Produto com ASIN '{asin}' não encontrado nesta wishlist.")
    
    return produto