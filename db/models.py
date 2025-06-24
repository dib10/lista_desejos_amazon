from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import os

SQLALCHEMY_DATABASE_URL = "sqlite:///./wishlist.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    asin = Column(String, unique=True, index=True, nullable=False)
    nome = Column(String, nullable=False)
    link_produto = Column(String, unique=True)
    link_imagem = Column(String)

    # Relacionamento: Informa ao SQLAlchemy que um Produto pode ter vários preços históricos.
    historico_precos = relationship("HistoricoPreco", back_populates="produto")


class HistoricoPreco(Base):
    __tablename__ = "historico_precos"

    id = Column(Integer, primary_key=True, index=True)
    preco = Column(Float, nullable=True) # Preço pode ser nulo se o item ficar indisponível
    data_extracao = Column(DateTime, default=datetime.utcnow)
    
    # Chave estrangeira
    produto_id = Column(Integer, ForeignKey("produtos.id"))

    # Relacionamento inverso
    produto = relationship("Produto", back_populates="historico_precos")