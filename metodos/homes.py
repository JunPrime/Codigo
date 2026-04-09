# metodos/Homes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List

from database import get_db
from modelos.modelos import Hogar, Usuario, Miembro
from esquemas.schemas import Hogar as HogarSchema, HogarCreate, Miembro as MiembroSchema
from metodos.auth import get_current_user

router = APIRouter(prefix="/hogares", tags=["Hogares"])

# GET /hogares - Listar hogares del usuario autenticado
@router.get("/", response_model=List[HogarSchema])
def listar_hogares(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    hogares = db.query(Hogar).filter(Hogar.id_usuario_f == current_user.id_usuario).all()
    return hogares

# POST /hogares - Crear un nuevo hogar (usando el SP CrearHogar)
@router.post("/", response_model=HogarSchema, status_code=status.HTTP_201_CREATED)
def crear_hogar(
    data: dict,  # espera {"nombre_hogar": "Familia Perez", "nombre_admin": "Admin"}
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    nombre_hogar = data.get("nombre_hogar")
    nombre_admin = data.get("nombre_admin")
    if not nombre_hogar or not nombre_admin:
        raise HTTPException(status_code=400, detail="Missing fields: nombre_hogar and nombre_admin")
    
    # Llamar al stored procedure CrearHogar
    try:
        db.execute(
            text("CALL CrearHogar(:p_id_usuario, :p_nombre_hogar, :p_nombre_admin)"),
            {
                "p_id_usuario": current_user.id_usuario,
                "p_nombre_hogar": nombre_hogar,
                "p_nombre_admin": nombre_admin
            }
        )
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating home: {str(e)}")
    
    # Obtener el hogar recién creado (último del usuario)
    nuevo_hogar = db.query(Hogar).filter(
        Hogar.id_usuario_f == current_user.id_usuario
    ).order_by(Hogar.id_hogar.desc()).first()
    
    if not nuevo_hogar:
        raise HTTPException(status_code=500, detail="Could not retrieve the created home")
    
    return nuevo_hogar

# GET /hogares/{idHogar} - Detalles de un hogar específico
@router.get("/{id_hogar}", response_model=HogarSchema)
def obtener_hogar(
    id_hogar: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    hogar = db.query(Hogar).filter(Hogar.id_hogar == id_hogar).first()
    if not hogar:
        raise HTTPException(status_code=404, detail="Home not found")
    if hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="You are not the owner of this home")
    return hogar


# PUT /hogares/{idHogar} - Actualizar nombre del hogar (solo propietario)
@router.put("/{id_hogar}", response_model=HogarSchema)
def actualizar_hogar(
    id_hogar: int,
    data: dict,  # espera {"nombre_familiar": "NuevoNombre"}
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    hogar = db.query(Hogar).filter(Hogar.id_hogar == id_hogar).first()
    if not hogar:
        raise HTTPException(status_code=404, detail="Home not found")
    if hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="You are not the owner of this home")
    
    nuevo_nombre = data.get("nombre_familiar")
    if nuevo_nombre is None:
        raise HTTPException(status_code=400, detail="The field 'nombre_familiar' is required")
    
    hogar.nombre_familiar = nuevo_nombre
    db.commit()
    db.refresh(hogar)
    return hogar



# DELETE /hogares/{idHogar} - Eliminar hogar (solo propietario, solo si no tiene datos relacionados)
@router.delete("/{id_hogar}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_hogar(
    id_hogar: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    hogar = db.query(Hogar).filter(Hogar.id_hogar == id_hogar).first()
    if not hogar:
        raise HTTPException(status_code=404, detail="Home not found")
    if hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="You are not the owner of this home")
    
    # Verificar si el hogar tiene datos relacionados (miembros, tareas, stock, etc.)
    # Por simplicidad, asumimos que no se puede eliminar si tiene miembros
    from modelos.modelos import Miembro  # importación local para evitar circular
    miembros = db.query(Miembro).filter(Miembro.id_hogar == id_hogar).first()
    if miembros:
        raise HTTPException(status_code=400, detail="Cannot delete home because it has associated members")
    
    db.delete(hogar)
    db.commit()
    return None


####################################


# GET /hogares/{idHogar}/miembros - Listar miembros de un hogar
@router.get("/{id_hogar}/miembros", response_model=List[MiembroSchema])
def listar_miembros(
    id_hogar: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verificar que el hogar existe y pertenece al usuario
    hogar = db.query(Hogar).filter(Hogar.id_hogar == id_hogar).first()
    if not hogar:
        raise HTTPException(status_code=404, detail="Home not found")
    if hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="You are not the owner of this home")
    
    miembros = db.query(Miembro).filter(Miembro.id_hogar == id_hogar).all()
    return miembros

# POST /hogares/{idHogar}/miembros - Agregar un nuevo miembro
@router.post("/{id_hogar}/miembros", response_model=MiembroSchema, status_code=201)
def agregar_miembro(
    id_hogar: int,
    data: dict,  # espera {"nombre": "Ana", "es_admin": false, "preferencias_alimenticias": "{}"}
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verificar propiedad del hogar
    hogar = db.query(Hogar).filter(Hogar.id_hogar == id_hogar).first()
    if not hogar or hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="You do not have permission to add members to this home")
    
    nombre = data.get("nombre")
    if not nombre:
        raise HTTPException(status_code=400, detail="The field 'nombre' is required")
    
    es_admin = data.get("es_admin", False)
    preferencias = data.get("preferencias_alimenticias", None)
    
    # Llamar al SP AgregarMiembro
    try:
        db.execute(
            text("CALL AgregarMiembro(:p_id_hogar, :p_nombre, :p_es_admin, :p_preferencias)"),
            {
                "p_id_hogar": id_hogar,
                "p_nombre": nombre,
                "p_es_admin": es_admin,
                "p_preferencias": preferencias
            }
        )
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding member: {str(e)}")
    
    # Recuperar el miembro recién creado (el último con ese nombre en el hogar)
    nuevo_miembro = db.query(Miembro).filter(
        Miembro.id_hogar == id_hogar,
        Miembro.nombre == nombre
    ).order_by(Miembro.id_miembro.desc()).first()
    
    if not nuevo_miembro:
        raise HTTPException(status_code=500, detail="Could not retrieve the created member")
    
    return nuevo_miembro