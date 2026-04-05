from pydantic import BaseModel
from typing import Optional, List
from datetime import date, time, datetime
from decimal import Decimal

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# ---------- Usuarios ----------
class UsuarioBase(BaseModel):
    nombre: str
    correo: str

class UsuarioCreate(UsuarioBase):
    contraseña: str

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    correo: Optional[str] = None
    contraseña: Optional[str] = None
    current_password: str   # obligatorio

class UsuarioSchema(UsuarioBase):
    id_usuario: int
    fecha_registro: Optional[datetime] = None

    class Config:
        orm_mode = True

# ---------- Tokens ------------
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int   # segundos

class PasswordVerify(BaseModel):
    password: str



# ---------- Hogares ----------
class HogarBase(BaseModel):
    nombre_familiar: Optional[str]

class HogarCreate(HogarBase):
    id_usuario_f: int

class Hogar(HogarBase):
    id_hogar: int
    id_usuario_f: int
    
    class Config:
        orm_mode = True

# ---------- Miembros ----------
class MiembroBase(BaseModel):
    nombre: str
    es_admin: Optional[bool] = False
    preferencias_alimenticias: Optional[str] = None
    activo: Optional[bool] = True

class MiembroCreate(MiembroBase):
    id_hogar: int

class Miembro(MiembroBase):
    id_miembro: int
    id_hogar: int
    
    class Config:
        orm_mode = True

# ---------- ConfiguracionMiembro ----------
class ConfiguracionMiembroBase(BaseModel):
    crear_actividad: bool = False
    crear_tarea: bool = False
    administrar_miembros: bool = False

class ConfiguracionMiembroCreate(ConfiguracionMiembroBase):
    id_miembro_f: int

class ConfiguracionMiembro(ConfiguracionMiembroBase):
    id_configuracion: int
    id_miembro_f: int
    
    class Config:
        orm_mode = True

# ---------- Tareas ----------

class TareaBase(BaseModel):
    nombre: str   # nuevo
    descripcion: Optional[str] = None   # nuevo
    repetitiva: Optional[int] = None
    realizada: Optional[bool] = False
    hora: Optional[time] = None   # opcional porque al crear sin asignar podría no tener hora
    fecha: Optional[date] = None   # opcional
    duracion_minutos: Optional[int] = None
    solo_adulto: Optional[bool] = False   # nuevo, según descripción

class TareaCreate(TareaBase):
    id_hogar_f: int
    id_miembro_f: Optional[int] = None   # opcional

class Tarea(TareaBase):
    id_tarea: int
    id_hogar_f: int
    id_miembro_f: Optional[int] = None
    
    class Config:
        orm_mode = True
# ---------- Actividades ----------
class ActividadBase(BaseModel):
    repetitiva_semanal: Optional[bool] = False
    hora: time
    dias_semana: Optional[str] = None
    duracion_minutos: Optional[int] = None
    economica: Optional[bool] = False

class ActividadCreate(ActividadBase):
    pass

class Actividad(ActividadBase):
    id_actividad: int
    id_miembro_f: int
    
    class Config:
        orm_mode = True

# ---------- SeguimientoMedico ----------
class SeguimientoMedicoBase(BaseModel):
    fecha: Optional[date] = None
    estado: Optional[str] = None
    nota: Optional[str] = None

class SeguimientoMedicoCreate(SeguimientoMedicoBase):
    id_miembro_f: int

class SeguimientoMedico(SeguimientoMedicoBase):
    id_seguimiento: int
    id_miembro_f: int
    
    class Config:
        orm_mode = True

# ---------- Mensualidades ----------
class MensualidadBase(BaseModel):
    valor_aproximado: Optional[Decimal] = None
    fecha_cancelacion: Optional[date] = None
    dias_repeticion: Optional[str] = None
    estado: Optional[bool] = False

class MensualidadCreate(MensualidadBase):
    id_hogar_f: int

class Mensualidad(MensualidadBase):
    id_mensualidad: int
    id_hogar_f: int
    
    class Config:
        orm_mode = True

# ---------- GastosMiembro ----------
class GastoMiembroBase(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    valor_aproximado: Optional[Decimal] = None

class GastoMiembroCreate(GastoMiembroBase):
    id_miembro_f: int

class GastoMiembro(GastoMiembroBase):
    id_gasto: int
    dia_registro: Optional[datetime]
    id_miembro_f: int
    
    class Config:
        orm_mode = True

# ---------- ClasificacionIngrediente ----------
class ClasificacionIngredienteBase(BaseModel):
    nombre: str

class ClasificacionIngredienteCreate(ClasificacionIngredienteBase):
    pass

class ClasificacionIngrediente(ClasificacionIngredienteBase):
    id_clasificacion: int
    
    class Config:
        orm_mode = True

# ---------- UnidadMedida ----------
class UnidadMedidaBase(BaseModel):
    nombre: str
    abreviatura: Optional[str] = None

class UnidadMedidaCreate(UnidadMedidaBase):
    pass

class UnidadMedida(UnidadMedidaBase):
    id_unidad: int
    
    class Config:
        orm_mode = True

# ---------- TipoIngrediente ----------
class TipoIngredienteBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    id_clasificacion: Optional[int] = None
    id_unidad_base: Optional[int] = None
    caducidad_estandar_dias: Optional[int] = None
    cantidad_minima_aviso: Optional[float] = 0.0

class TipoIngredienteCreate(TipoIngredienteBase):
    pass

class TipoIngrediente(TipoIngredienteBase):
    id_tipo_ingrediente: int
    
    class Config:
        orm_mode = True

# ---------- StockIngrediente ----------
class StockIngredienteBase(BaseModel):
    cantidad: float = 0.0
    fecha_caducidad: Optional[date] = None

class StockIngredienteCreate(StockIngredienteBase):
    id_hogar: int
    id_tipo_ingrediente: int
    id_unidad: Optional[int] = None

class StockIngrediente(StockIngredienteBase):
    id_stock: int
    id_hogar: int
    id_tipo_ingrediente: int
    id_unidad: Optional[int]
    fecha_registro: Optional[datetime]
    
    class Config:
        orm_mode = True

# ---------- HistorialConsumo ----------
class HistorialConsumoBase(BaseModel):
    cantidad_consumida: float
    fecha_consumo: date

class HistorialConsumoCreate(HistorialConsumoBase):
    id_hogar: int
    id_tipo_ingrediente: int
    id_unidad: int

class HistorialConsumo(HistorialConsumoBase):
    id_consumo: int
    id_hogar: int
    id_tipo_ingrediente: int
    id_unidad: int
    
    class Config:
        orm_mode = True

# ---------- Esquemas para respuestas compuestas (ejemplo) ----------
class StockDisponible(BaseModel):
    id_hogar: int
    id_tipo_ingrediente: int
    nombre_ingrediente: str
    id_unidad_base: int
    cantidad_minima_aviso: float
    cantidad_total: float
    proxima_caducidad: Optional[date]

    class Config:
        orm_mode = True

# Para consumir ingredientes (body esperado)
class ConsumoItem(BaseModel):
    id_tipo_ingrediente: int
    cantidad: float
    id_unidad: int

class ConsumoRequest(BaseModel):
    consumos: List[ConsumoItem]