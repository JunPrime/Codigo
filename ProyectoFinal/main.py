from fastapi import FastAPI, Depends

from metodos import auth , homes , miembros, tareas, actividades

app = FastAPI()
app.include_router(auth.router, prefix="/Sesion")
app.include_router(homes.router, prefix="/hogares")
app.include_router(miembros.router, prefix="/miembros")
app.include_router(tareas.router, prefix="/tareas")
app.include_router(actividades.router, prefix="/actividades")