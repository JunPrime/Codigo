from fastapi import FastAPI, Depends
from metodos import auth, homes, miembros, tareas, actividades
from database import Base, engine
from modelos import modelos  # importa los modelos

# Crear tablas en la BD
Base.metadata.create_all(bind=engine)

app = FastAPI()
z
@app.get("/ping")
def ping():
    return {"message": "pong"}

app.include_router(auth.router, prefix="/Sesion")
app.include_router(homes.router, prefix="/hogares")
app.include_router(miembros.router, prefix="/miembros")
app.include_router(tareas.router, prefix="/tareas")
app.include_router(actividades.router, prefix="/actividades")
