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

class Wishlist(Base):
    __tablename__ = "wishlists"

    id = Column(Integer, primary_key=True, index=True)
    nome_wishlist = Column(String, nullable=False) 
    url = Column(String, unique=True, nullable=False)
    produtos = relationship("Produto", back_populates="wishlist", cascade="all, delete-orphan")
    historico_precos = relationship("HistoricoPreco", back_populates="wishlist", cascade="all, delete-orphan")


class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    asin = Column(String,index=True, nullable=False)
    nome = Column(String, nullable=False)
    link_produto = Column(String)
    link_imagem = Column(String)

    wishlist_id = Column(Integer, ForeignKey("wishlists.id"), nullable=False)
    wishlist = relationship("Wishlist", back_populates="produtos")

 
    historico_precos = relationship("HistoricoPreco", back_populates="produto", cascade="all, delete-orphan")


class HistoricoPreco(Base):
    __tablename__ = "historico_precos"

    id = Column(Integer, primary_key=True, index=True)
    preco = Column(Float, nullable=True) 
    data_extracao = Column(DateTime, default=datetime.utcnow)
    produto_id = Column(Integer, ForeignKey("produtos.id"))

    produto = relationship("Produto", back_populates="historico_precos")

    wishlist_id = Column(Integer, ForeignKey("wishlists.id"), nullable=False)
    wishlist = relationship("Wishlist", back_populates="historico_precos")