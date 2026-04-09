from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from modelos.modelos import Miembro, ConfiguracionMiembro, Usuario, Hogar
from esquemas.schemas import Miembro as MiembroSchema, ConfiguracionMiembro as ConfigSchema
from metodos.auth import get_current_user

router = APIRouter(prefix="/miembros", tags=["Miembros"])

# GET /miembros/{idMiembro} - Obtener detalles de un miembro
@router.get("/{id_miembro}", response_model=MiembroSchema)
def obtener_miembro(
    id_miembro: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    miembro = db.query(Miembro).filter(Miembro.id_miembro == id_miembro).first()
    if not miembro:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Verificar que el usuario sea propietario del hogar
    hogar = db.query(Hogar).filter(Hogar.id_hogar == miembro.id_hogar).first()
    if hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="You do not have permission to view this member")
    
    return miembro

# PUT /miembros/{idMiembro} - Actualizar nombre, rol, preferencias, activo
@router.put("/{id_miembro}", response_model=MiembroSchema)
def actualizar_miembro(
    id_miembro: int,
    data: dict,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    miembro = db.query(Miembro).filter(Miembro.id_miembro == id_miembro).first()
    if not miembro:
        raise HTTPException(status_code=404, detail="Member not found")
    
    hogar = db.query(Hogar).filter(Hogar.id_hogar == miembro.id_hogar).first()
    if hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="You do not have permission to modify this member")
    
    # Actualizar campos si están presentes
    if "nombre" in data:
        miembro.nombre = data["nombre"]
    if "es_admin" in data:
        miembro.es_admin = data["es_admin"]
    if "preferencias_alimenticias" in data:
        miembro.preferencias_alimenticias = data["preferencias_alimenticias"]
    if "activo" in data:
        miembro.activo = data["activo"]
    
    db.commit()
    db.refresh(miembro)
    return miembro

# DELETE /miembros/{idMiembro} - Desactivar o eliminar miembro
@router.delete("/{id_miembro}", status_code=status.HTTP_200_OK)
def eliminar_miembro(
    id_miembro: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    miembro = db.query(Miembro).filter(Miembro.id_miembro == id_miembro).first()
    if not miembro:
        raise HTTPException(status_code=404, detail="Member not found")
    
    hogar = db.query(Hogar).filter(Hogar.id_hogar == miembro.id_hogar).first()
    if hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this member")
    
    db.query(ConfiguracionMiembro).filter(
        ConfiguracionMiembro.id_miembro_f == id_miembro
    ).delete()
    db.delete(miembro)
    db.commit()
    return {"message": "Member deleted successfully"}

# GET /miembros/{idMiembro}/configuracion - Obtener permisos
@router.get("/{id_miembro}/configuracion", response_model=ConfigSchema)
def obtener_configuracion(
    id_miembro: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    miembro = db.query(Miembro).filter(Miembro.id_miembro == id_miembro).first()
    if not miembro:
        raise HTTPException(status_code=404, detail="Member not found")
    
    hogar = db.query(Hogar).filter(Hogar.id_hogar == miembro.id_hogar).first()
    if hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="You do not have permission")
    
    config = db.query(ConfiguracionMiembro).filter(
        ConfiguracionMiembro.id_miembro_f == id_miembro
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    return config

# PUT /miembros/{idMiembro}/configuracion - Actualizar permisos
@router.put("/{id_miembro}/configuracion", response_model=ConfigSchema)
def actualizar_configuracion(
    id_miembro: int,
    data: dict,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    miembro = db.query(Miembro).filter(Miembro.id_miembro == id_miembro).first()
    if not miembro:
        raise HTTPException(status_code=404, detail="Member not found")
    
    hogar = db.query(Hogar).filter(Hogar.id_hogar == miembro.id_hogar).first()
    if hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="You do not have permission")
    
    config = db.query(ConfiguracionMiembro).filter(
        ConfiguracionMiembro.id_miembro_f == id_miembro
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    # Actualizar campos
    if "crear_actividad" in data:
        config.crear_actividad = data["crear_actividad"]
    if "crear_tarea" in data:
        config.crear_tarea = data["crear_tarea"]
    if "administrar_miembros" in data:
        config.administrar_miembros = data["administrar_miembros"]
    
    db.commit()
    db.refresh(config)
    return config