from db.models import Base, engine

print("Iniciando a criação das tabelas no banco de dados...")

Base.metadata.create_all(bind=engine)

print("Tabelas criadas com sucesso!")