from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from database import get_db
from modelos.modelos import Tarea, Miembro, Hogar, Usuario
from esquemas.schemas import Tarea as TareaSchema, TareaCreate
from metodos.auth import get_current_user

router = APIRouter(tags=["Tareas"])

# ---------- Endpoints que empiezan con /hogares/{idHogar}/tareas ----------
@router.get("/hogares/{id_hogar}/tareas", response_model=List[TareaSchema])
def listar_tareas_hogar(
    id_hogar: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verificar que el hogar pertenece al usuario
    hogar = db.query(Hogar).filter(Hogar.id_hogar == id_hogar).first()
    if not hogar or hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="No tienes permiso para ver tareas de este hogar")
    
    tareas = db.query(Tarea).filter(Tarea.id_hogar_f == id_hogar).all()
    return tareas

@router.post("/hogares/{id_hogar}/tareas", response_model=TareaSchema, status_code=201)
def crear_tarea(
    id_hogar: int,
    tarea_data: TareaCreate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verificar propiedad del hogar
    hogar = db.query(Hogar).filter(Hogar.id_hogar == id_hogar).first()
    if not hogar or hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="No eres propietario de este hogar")
    
    # Si se especificó id_miembro_f, verificar que pertenezca al hogar
    if tarea_data.id_miembro_f:
        miembro = db.query(Miembro).filter(
            Miembro.id_miembro == tarea_data.id_miembro_f,
            Miembro.id_hogar == id_hogar
        ).first()
        if not miembro:
            raise HTTPException(status_code=400, detail="El miembro no pertenece a este hogar")
    
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

# ---------- Endpoints de tareas individuales ----------
@router.put("/tareas/{id_tarea}", response_model=TareaSchema)
def actualizar_tarea(
    id_tarea: int,
    tarea_data: TareaCreate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tarea = db.query(Tarea).filter(Tarea.id_tarea == id_tarea).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    # Verificar que el usuario sea propietario del hogar
    hogar = db.query(Hogar).filter(Hogar.id_hogar == tarea.id_hogar_f).first()
    if hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="No tienes permiso para modificar esta tarea")
    
    # Actualizar campos
    for key, value in tarea_data.dict(exclude_unset=True).items():
        setattr(tarea, key, value)
    
    db.commit()
    db.refresh(tarea)
    return tarea

@router.delete("/tareas/{id_tarea}", status_code=204)
def eliminar_tarea(
    id_tarea: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tarea = db.query(Tarea).filter(Tarea.id_tarea == id_tarea).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    hogar = db.query(Hogar).filter(Hogar.id_hogar == tarea.id_hogar_f).first()
    if hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar esta tarea")
    
    # Verificar si tiene asignaciones futuras (asumimos que siempre se puede eliminar)
    db.delete(tarea)
    db.commit()
    return None

@router.post("/tareas/{id_tarea}/asignar", response_model=TareaSchema)
def asignar_tarea(
    id_tarea: int,
    data: dict,  # { id_miembro, fecha, hora, duracion_minutos, repetitiva }
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tarea = db.query(Tarea).filter(Tarea.id_tarea == id_tarea).first()
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    hogar = db.query(Hogar).filter(Hogar.id_hogar == tarea.id_hogar_f).first()
    if hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="No tienes permiso para asignar esta tarea")
    
    id_miembro = data.get("id_miembro")
    if not id_miembro:
        raise HTTPException(status_code=400, detail="Se requiere id_miembro")
    
    # Verificar que el miembro pertenece al hogar
    miembro = db.query(Miembro).filter(Miembro.id_miembro == id_miembro, Miembro.id_hogar == tarea.id_hogar_f).first()
    if not miembro:
        raise HTTPException(status_code=400, detail="El miembro no pertenece al hogar")
    
    # Actualizar tarea
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
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    hogar = db.query(Hogar).filter(Hogar.id_hogar == tarea.id_hogar_f).first()
    if hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="No tienes permiso para completar esta tarea")
    
    tarea.realizada = True
    db.commit()
    db.refresh(tarea)
    return tarea

# ---------- Endpoint de tareas pendientes por miembro ----------
@router.get("/miembros/{id_miembro}/tareas/pendientes", response_model=List[TareaSchema])
def tareas_pendientes_miembro(
    id_miembro: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verificar que el miembro existe y que el usuario es propietario del hogar
    miembro = db.query(Miembro).filter(Miembro.id_miembro == id_miembro).first()
    if not miembro:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")
    
    hogar = db.query(Hogar).filter(Hogar.id_hogar == miembro.id_hogar).first()
    if hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="No tienes permiso para ver las tareas de este miembro")
    
    hoy = date.today()
    tareas = db.query(Tarea).filter(
        Tarea.id_miembro_f == id_miembro,
        Tarea.realizada == False,
        Tarea.fecha <= hoy
    ).order_by(Tarea.fecha, Tarea.hora).all()
    
    return tareas