from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from modelos.modelos import Actividad, Miembro, Hogar, Usuario
from esquemas.schemas import Actividad as ActividadSchema, ActividadCreate
from metodos.auth import get_current_user

router = APIRouter(prefix="/actividades", tags=["Actividades Personales"])

# GET /miembros/{idMiembro}/actividades - List activities of a member
@router.get("/miembros/{id_miembro}/actividades", response_model=List[ActividadSchema])
def listar_actividades(
    id_miembro: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify that the member exists
    miembro = db.query(Miembro).filter(Miembro.id_miembro == id_miembro).first()
    if not miembro:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Verify that the user is the owner of the member's home
    hogar = db.query(Hogar).filter(Hogar.id_hogar == miembro.id_hogar).first()
    if hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="You do not have permission to view activities for this member")
    
    actividades = db.query(Actividad).filter(Actividad.id_miembro_f == id_miembro).all()
    return actividades

# POST /miembros/{idMiembro}/actividades - Create an activity for a member
@router.post("/miembros/{id_miembro}/actividades", response_model=ActividadSchema, status_code=201)
def crear_actividad(
    id_miembro: int,
    actividad_data: ActividadCreate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify that the member exists
    miembro = db.query(Miembro).filter(Miembro.id_miembro == id_miembro).first()
    if not miembro:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Verify ownership of the home
    hogar = db.query(Hogar).filter(Hogar.id_hogar == miembro.id_hogar).first()
    if hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="You do not have permission to create activities for this member")
    
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

# PUT /actividades/{idActividad} - Update an activity
@router.put("/{id_actividad}", response_model=ActividadSchema)
def actualizar_actividad(
    id_actividad: int,
    actividad_data: ActividadCreate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    actividad = db.query(Actividad).filter(Actividad.id_actividad == id_actividad).first()
    if not actividad:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # Verify that the user is the owner of the home associated with the member
    miembro = db.query(Miembro).filter(Miembro.id_miembro == actividad.id_miembro_f).first()
    hogar = db.query(Hogar).filter(Hogar.id_hogar == miembro.id_hogar).first()
    if hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="You do not have permission to modify this activity")
    
    # Update fields
    actividad.repetitiva_semanal = actividad_data.repetitiva_semanal
    actividad.hora = actividad_data.hora
    actividad.dias_semana = actividad_data.dias_semana
    actividad.duracion_minutos = actividad_data.duracion_minutos
    actividad.economica = actividad_data.economica
    
    db.commit()
    db.refresh(actividad)
    return actividad

# DELETE /actividades/{idActividad} - Delete an activity
@router.delete("/{id_actividad}", status_code=204)
def eliminar_actividad(
    id_actividad: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    actividad = db.query(Actividad).filter(Actividad.id_actividad == id_actividad).first()
    if not actividad:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # Verify permission
    miembro = db.query(Miembro).filter(Miembro.id_miembro == actividad.id_miembro_f).first()
    hogar = db.query(Hogar).filter(Hogar.id_hogar == miembro.id_hogar).first()
    if hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this activity")
    
    db.delete(actividad)
    db.commit()
    return None