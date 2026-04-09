from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from database import get_db
from modelos.modelos import Tarea, Miembro, Hogar, Usuario
from esquemas.schemas import Tarea as TareaSchema, TareaCreate
from metodos.auth import get_current_user

router = APIRouter(tags=["Tareas"])

# ---------- Endpoints that start with /hogares/{idHogar}/tareas ----------
@router.get("/hogares/{id_hogar}/tareas", response_model=List[TareaSchema])
def listar_tareas_hogar(
    id_hogar: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify that the home belongs to the user
    hogar = db.query(Hogar).filter(Hogar.id_hogar == id_hogar).first()
    if not hogar or hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=400, detail="You do not have permission to view tasks for this home")
    
    tareas = db.query(Tarea).filter(Tarea.id_hogar_f == id_hogar).all()
    return tareas

@router.post("/hogares/{id_hogar}/tareas", response_model=TareaSchema)
def crear_tarea(
    id_hogar: int,
    tarea_data: TareaCreate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify home ownership
    hogar = db.query(Hogar).filter(Hogar.id_hogar == id_hogar).first()
    if not hogar or hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=400, detail="You are not the owner of this home")
    
    # If id_miembro_f is specified, verify it belongs to the home
    if tarea_data.id_miembro_f:
        miembro = db.query(Miembro).filter(
            Miembro.id_miembro == tarea_data.id_miembro_f,
            Miembro.id_hogar == id_hogar
        ).first()
        if not miembro:
            raise HTTPException(status_code=400, detail="The member does not belong to this home")
    
    nueva_tarea = Tarea(
        nombre=tarea_data.nombre,
        descripcion=tarea_data.descripcion,
        solo_adulto=tarea_data.solo_adulto,
        repetitiva=tarea_data.repetitiva,
        realizada=False,
        hora=tarea_data.hora,
        fecha=tarea_data.fecha,
        duracion_minutos=tarea_data.duracion_minutos,
        id_miembro_f=tarea_data.id_miembro_f,
        id_hogar_f=id_hogar
    )
    db.add(nueva_tarea)
    db.commit()
    db.refresh(nueva_tarea)
    return nueva_tarea

# ---------- Individual task endpoints ----------
@router.put("/tareas/{id_tarea}", response_model=TareaSchema)
def actualizar_tarea(
    id_tarea: int,
    tarea_data: TareaCreate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tarea = db.query(Tarea).filter(Tarea.id_tarea == id_tarea).first()
    if not tarea:
        raise HTTPException(status_code=400, detail="Task not found")
    
    # Verify that the user is the owner of the home
    hogar = db.query(Hogar).filter(Hogar.id_hogar == tarea.id_hogar_f).first()
    if hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=400, detail="You do not have permission to modify this task")
    
    # Update fields
    for key, value in tarea_data.dict(exclude_unset=True).items():
        setattr(tarea, key, value)
    
    db.commit()
    db.refresh(tarea)
    return tarea

@router.delete("/tareas/{id_tarea}")
def eliminar_tarea(
    id_tarea: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tarea = db.query(Tarea).filter(Tarea.id_tarea == id_tarea).first()
    if not tarea:
        raise HTTPException(status_code=400, detail="Task not found")
    
    hogar = db.query(Hogar).filter(Hogar.id_hogar == tarea.id_hogar_f).first()
    if hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=400, detail="You do not have permission to delete this task")
    
    db.delete(tarea)
    db.commit()
    return {"detail": "Task deleted successfully"}

@router.post("/tareas/{id_tarea}/asignar", response_model=TareaSchema)
def asignar_tarea(
    id_tarea: int,
    data: dict,  # { id_miembro, fecha, hora, duracion_minutos, repetitiva }
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tarea = db.query(Tarea).filter(Tarea.id_tarea == id_tarea).first()
    if not tarea:
        raise HTTPException(status_code=400, detail="Task not found")
    
    hogar = db.query(Hogar).filter(Hogar.id_hogar == tarea.id_hogar_f).first()
    if hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=400, detail="You do not have permission to assign this task")
    
    id_miembro = data.get("id_miembro")
    if not id_miembro:
        raise HTTPException(status_code=400, detail="id_miembro is required")
    
    # Verify that the member belongs to the home
    miembro = db.query(Miembro).filter(Miembro.id_miembro == id_miembro, Miembro.id_hogar == tarea.id_hogar_f).first()
    if not miembro:
        raise HTTPException(status_code=400, detail="The member does not belong to the home")
    
    # Update task
    tarea.id_miembro_f = id_miembro
    tarea.fecha = data.get("fecha")
    tarea.hora = data.get("hora")
    tarea.duracion_minutos = data.get("duracion_minutos")
    tarea.repetitiva = data.get("repetitiva")
    tarea.realizada = False
    
    db.commit()
    db.refresh(tarea)
    return tarea

@router.put("/tareas/{id_tarea}/completar", response_model=TareaSchema)
def completar_tarea(
    id_tarea: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tarea = db.query(Tarea).filter(Tarea.id_tarea == id_tarea).first()
    if not tarea:
        raise HTTPException(status_code=400, detail="Task not found")
    
    hogar = db.query(Hogar).filter(Hogar.id_hogar == tarea.id_hogar_f).first()
    if hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=400, detail="You do not have permission to complete this task")
    
    tarea.realizada = True
    db.commit()
    db.refresh(tarea)
    return tarea

# ---------- Endpoint for pending tasks by member ----------
@router.get("/miembros/{id_miembro}/tareas/pendientes", response_model=List[TareaSchema])
def tareas_pendientes_miembro(
    id_miembro: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify that the member exists and the user is the home owner
    miembro = db.query(Miembro).filter(Miembro.id_miembro == id_miembro).first()
    if not miembro:
        raise HTTPException(status_code=400, detail="Member not found")
    
    hogar = db.query(Hogar).filter(Hogar.id_hogar == miembro.id_hogar).first()
    if hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=400, detail="You do not have permission to view tasks for this member")
    
    hoy = date.today()
    tareas = db.query(Tarea).filter(
        Tarea.id_miembro_f == id_miembro,
        Tarea.realizada == False,
        Tarea.fecha <= hoy
    ).order_by(Tarea.fecha, Tarea.hora).all()
    
    return tareas