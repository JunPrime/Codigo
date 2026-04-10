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
@router.post(
    "/miembros/{id_miembro}/gastos",
    response_model=GastoMiembroSchema,
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
    # Verify member exists
    miembro = db.query(Miembro).filter(Miembro.id_miembro == id_miembro).first()
    if not miembro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # Verify home ownership
    hogar = db.query(Hogar).filter(Hogar.id_hogar == miembro.id_hogar).first()
    if hogar.id_usuario_f != current_user.id_usuario:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to add expenses for this member"
        )
    
    nuevo_gasto = GastoMiembro(
        titulo=gasto_data.titulo,
        descripcion=gasto_data.descripcion,
        valor_aproximado=gasto_data.valor_aproximado,
        id_miembro_f=id_miembro
    )
    db.add(nuevo_gasto)
    db.commit()
    db.refresh(nuevo_gasto)
    return nuevo_gasto

# ----------------------------------------------------------------------
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