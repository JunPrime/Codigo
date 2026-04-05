from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from modelos.modelos import Actividad, Miembro, Hogar, Usuario
from esquemas.schemas import Actividad as ActividadSchema, ActividadCreate
from metodos.auth import get_current_user

router = APIRouter(prefix="/actividades", tags=["Actividades Personales"])

# GET /miembros/{idMiembro}/actividades - Listar actividades de un miembro
@router.get("/miembros/{id_miembro}/actividades", response_model=List[ActividadSchema])
def listar_actividades(
    id_miembro: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verificar que el miembro existe
    miembro = db.query(Miembro).filter(Miembro.id_miembro == id_miembro).first()
    if not miembro:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")
    
    # Verificar que el usuario es propietario del hogar del miembro
    hogar = db.query(Hogar).filter(Hogar.id_hogar == miembro.id_hogar).first()
    if hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="No tienes permiso para ver actividades de este miembro")
    
    actividades = db.query(Actividad).filter(Actividad.id_miembro_f == id_miembro).all()
    return actividades

# POST /miembros/{idMiembro}/actividades - Crear una actividad para un miembro
@router.post("/miembros/{id_miembro}/actividades", response_model=ActividadSchema, status_code=201)
def crear_actividad(
    id_miembro: int,
    actividad_data: ActividadCreate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verificar que el miembro existe
    miembro = db.query(Miembro).filter(Miembro.id_miembro == id_miembro).first()
    if not miembro:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")
    
    # Verificar propiedad del hogar
    hogar = db.query(Hogar).filter(Hogar.id_hogar == miembro.id_hogar).first()
    if hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="No tienes permiso para crear actividades para este miembro")
    
    nueva_actividad = Actividad(
        repetitiva_semanal=actividad_data.repetitiva_semanal,
        hora=actividad_data.hora,
        dias_semana=actividad_data.dias_semana,
        duracion_minutos=actividad_data.duracion_minutos,
        economica=actividad_data.economica,
        id_miembro_f=id_miembro
    )
    db.add(nueva_actividad)
    db.commit()
    db.refresh(nueva_actividad)
    return nueva_actividad

# PUT /actividades/{idActividad} - Actualizar una actividad
@router.put("/{id_actividad}", response_model=ActividadSchema)
def actualizar_actividad(
    id_actividad: int,
    actividad_data: ActividadCreate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    actividad = db.query(Actividad).filter(Actividad.id_actividad == id_actividad).first()
    if not actividad:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    
    # Verificar que el usuario es propietario del hogar del miembro asociado
    miembro = db.query(Miembro).filter(Miembro.id_miembro == actividad.id_miembro_f).first()
    hogar = db.query(Hogar).filter(Hogar.id_hogar == miembro.id_hogar).first()
    if hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="No tienes permiso para modificar esta actividad")
    
    # Actualizar campos
    actividad.repetitiva_semanal = actividad_data.repetitiva_semanal
    actividad.hora = actividad_data.hora
    actividad.dias_semana = actividad_data.dias_semana
    actividad.duracion_minutos = actividad_data.duracion_minutos
    actividad.economica = actividad_data.economica
    
    db.commit()
    db.refresh(actividad)
    return actividad

# DELETE /actividades/{idActividad} - Eliminar actividad
@router.delete("/{id_actividad}", status_code=204)
def eliminar_actividad(
    id_actividad: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    actividad = db.query(Actividad).filter(Actividad.id_actividad == id_actividad).first()
    if not actividad:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    
    # Verificar permiso
    miembro = db.query(Miembro).filter(Miembro.id_miembro == actividad.id_miembro_f).first()
    hogar = db.query(Hogar).filter(Hogar.id_hogar == miembro.id_hogar).first()
    if hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar esta actividad")
    
    db.delete(actividad)
    db.commit()
    return None