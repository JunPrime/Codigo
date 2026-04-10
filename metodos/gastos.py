from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import date
from decimal import Decimal

from database import get_db
from modelos.modelos import GastoMiembro, Miembro, Hogar, Usuario
from esquemas.schemas import GastoMiembro as GastoMiembroSchema, GastoMiembroCreate
from metodos.auth import get_current_user

router = APIRouter(prefix="/gastos", tags=["Gastos y Economía"])

# ----------------------------------------------------------------------
# GET /miembros/{id_miembro}/gastos
# ----------------------------------------------------------------------
@router.get(
    "/miembros/{id_miembro}/gastos",
    response_model=List[GastoMiembroSchema],
    status_code=status.HTTP_200_OK,
    summary="List personal expenses of a member",
    description="Returns all expenses registered for a specific member. Requires authentication and ownership of the member's home."
)
def listar_gastos_miembro(
    id_miembro: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify member exists
    miembro = db.query(Miembro).filter(Miembro.id_miembro == id_miembro).first()
    if not miembro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # Verify user owns the home
    hogar = db.query(Hogar).filter(Hogar.id_hogar == miembro.id_hogar).first()
    if hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view expenses of this member"
        )
    
    gastos = db.query(GastoMiembro).filter(GastoMiembro.id_miembro_f == id_miembro).order_by(GastoMiembro.dia_registro.desc()).all()
    return gastos

# ----------------------------------------------------------------------
# POST /miembros/{id_miembro}/gastos
# ----------------------------------------------------------------------
import logging

# Configurar logging básico (puedes ajustarlo)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post(
    "/miembros/{id_miembro}/gastos",
    response_model=GastoMiembroSchema,  # asegúrate de que sea el esquema correcto
    status_code=status.HTTP_201_CREATED,
    summary="Register a new expense for a member",
    description="Creates a new expense record linked to a member. Requires authentication and home ownership."
)
def registrar_gasto(
    id_miembro: int,
    gasto_data: GastoMiembroCreate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"=== Registrar gasto para miembro {id_miembro} ===")
    logger.info(f"Usuario autenticado: id={current_user.id_usuario}, nombre={current_user.nombre}")
    
    # Verify member exists
    miembro = db.query(Miembro).filter(Miembro.id_miembro == id_miembro).first()
    if not miembro:
        logger.warning(f"Miembro {id_miembro} no encontrado")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    logger.info(f"Miembro encontrado: id={miembro.id_miembro}, nombre={miembro.nombre}, id_hogar={miembro.id_hogar}")
    
    # Verify home ownership
    hogar = db.query(Hogar).filter(Hogar.id_hogar == miembro.id_hogar).first()
    if not hogar:
        logger.error(f"Hogar {miembro.id_hogar} no encontrado para el miembro {id_miembro}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Home not found for this member"
        )
    logger.info(f"Hogar encontrado: id={hogar.id_hogar}, id_usuario_f={hogar.id_usuario_f}")
    
    if hogar.id_usuario_f != current_user.id_usuario:
        logger.warning(f"Permiso denegado: usuario {current_user.id_usuario} no es propietario del hogar {hogar.id_hogar} (propietario={hogar.id_usuario_f})")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to add expenses for this member"
        )
    
    # Crear nuevo gasto
    nuevo_gasto = GastoMiembro(
        titulo=gasto_data.titulo,
        descripcion=gasto_data.descripcion,
        valor_aproximado=gasto_data.valor_aproximado,
        id_miembro_f=id_miembro
    )
    db.add(nuevo_gasto)
    db.commit()
    db.refresh(nuevo_gasto)
    logger.info(f"Gasto creado con id {nuevo_gasto.id_gasto} para miembro {id_miembro}")
    return nuevo_gasto
# GET /hogares/{id_hogar}/reporte-gastos
# ----------------------------------------------------------------------
@router.get(
    "/hogares/{id_hogar}/reporte-gastos",
    status_code=status.HTTP_200_OK,
    summary="Get expense report by member for a home",
    description="Calls the stored procedure 'ReporteGastosPorMiembro' to obtain total expenses grouped by member within a date range. Requires home ownership."
)
def reporte_gastos_hogar(
    id_hogar: int,
    fecha_inicio: date = Query(..., description="Start date (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., description="End date (YYYY-MM-DD)"),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify home exists and user is owner
    hogar = db.query(Hogar).filter(Hogar.id_hogar == id_hogar).first()
    if not hogar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Home not found"
        )
    if hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the owner of this home"
        )
    
    # Validate date range
    if fecha_inicio > fecha_fin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before or equal to end date"
        )
    
    try:
        result = db.execute(
            text("CALL ReporteGastosPorMiembro(:p_id_hogar, :p_fecha_inicio, :p_fecha_fin)"),
            {
                "p_id_hogar": id_hogar,
                "p_fecha_inicio": fecha_inicio,
                "p_fecha_fin": fecha_fin
            }
        )
        reporte = result.fetchall()
        db.commit()  # Close cursor
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate expense report: {str(e)}"
        )
    
    # Format response
    return [
        {
            "member": row[0],
            "total_spent": float(row[1]) if row[1] else 0.0
        }
        for row in reporte
    ]