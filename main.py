from fastapi import FastAPI, Depends
from metodos import auth, homes, miembros, tareas, actividades, gastos
from database import Base, engine
from modelos import modelos  # importa los modelos
from fastapi.middleware.cors import CORSMiddleware

# Crear tablas en la BD
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",           # Sin slash al final
        "http://127.0.0.1:5500",           # Sin slash al final
        "http://localhost:4200",           # Sin slash al final
        "http://127.0.0.1:4200",           # Sin slash al final
        "https://junprime.github.io",      # Sin slash al final
        "https://junprime.github.io/Domus" # Sin slash al final
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Incluye OPTIONS
    allow_headers=["*"],  
)

@app.get("/ping")
def ping():
    return {"message": "pong"}

app.include_router(auth.router, prefix="/Sesion")
app.include_router(homes.router, prefix="/hogares")
app.include_router(miembros.router, prefix="/miembros")
app.include_router(tareas.router, prefix="/tareas")
app.include_router(actividades.router, prefix="/actividades")
app.include_router(gastos.router, prefix="/gastos")