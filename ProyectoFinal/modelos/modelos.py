from sqlalchemy import Column, Integer, String, Boolean, Float, Date, Time, TIMESTAMP, ForeignKey, Text, DECIMAL, Enum, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime


Base = declarative_base()


class Usuario(Base):
    __tablename__ = "usuarios"
    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False)
    correo = Column(String(150), unique=True, nullable=False)
    contraseña = Column(String(255), nullable=False)  # luego se hashea
    fecha_registro = Column(TIMESTAMP, default=datetime.utcnow)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(500), unique=True, nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)
    
    usuario = relationship("Usuario", backref="refresh_tokens")

class Hogar(Base):
    __tablename__ = "hogares"
    id_hogar = Column(Integer, primary_key=True, index=True)
    id_usuario_f = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    nombre_familiar = Column(String(50))
    
    # relaciones
    propietario = relationship("Usuario", backref="hogares")

class Miembro(Base):
    __tablename__ = "miembros"
    id_miembro = Column(Integer, primary_key=True, index=True)
    id_hogar = Column(Integer, ForeignKey("hogares.id_hogar"), nullable=False)
    nombre = Column(String(50), nullable=False)
    es_admin = Column(Boolean, default=False)
    preferencias_alimenticias = Column(Text)  # JSON string
    activo = Column(Boolean, default=True)
    
    # relaciones
    hogar = relationship("Hogar", backref="miembros")

class ConfiguracionMiembro(Base):
    __tablename__ = "configuracion_miembro"
    id_configuracion = Column(Integer, primary_key=True, index=True)
    crear_actividad = Column(Boolean, nullable=False, default=False)
    crear_tarea = Column(Boolean, nullable=False, default=False)
    administrar_miembros = Column(Boolean, nullable=False, default=False)
    id_miembro_f = Column(Integer, ForeignKey("miembros.id_miembro"), nullable=False)
    
    miembro = relationship("Miembro", backref="configuracion")

class Tarea(Base):
    __tablename__ = "tareas"
    id_tarea = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)   # nuevo
    descripcion = Column(Text)   # nuevo
    solo_adulto = Column(Boolean, default=False)   # nuevo
    repetitiva = Column(Integer, default=None)
    realizada = Column(Boolean, default=False)
    hora = Column(Time, nullable=True)   # cambiar a nullable
    fecha = Column(Date, nullable=True)   # cambiar a nullable
    duracion_minutos = Column(Integer)
    id_miembro_f = Column(Integer, ForeignKey("miembros.id_miembro"), nullable=True)   # cambiar a nullable
    id_hogar_f = Column(Integer, ForeignKey("hogares.id_hogar"), nullable=False)
    
    miembro = relationship("Miembro", backref="tareas")
    hogar = relationship("Hogar", backref="tareas")

class Actividad(Base):
    __tablename__ = "actividades"
    id_actividad = Column(Integer, primary_key=True, index=True)
    repetitiva_semanal = Column(Boolean, default=False)
    hora = Column(Time, nullable=False)
    dias_semana = Column(Text)  # almacenar como "1,2,3" o JSON
    duracion_minutos = Column(Integer)
    economica = Column(Boolean, default=False)
    id_miembro_f = Column(Integer, ForeignKey("miembros.id_miembro"), nullable=False)
    
    miembro = relationship("Miembro", backref="actividades")

class SeguimientoMedico(Base):
    __tablename__ = "seguimiento_medico"
    id_seguimiento = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date)
    estado = Column(String(50))
    nota = Column(String(500))
    id_miembro_f = Column(Integer, ForeignKey("miembros.id_miembro"), nullable=False)
    
    miembro = relationship("Miembro", backref="seguimientos")

class Mensualidad(Base):
    __tablename__ = "mensualidades"
    id_mensualidad = Column(Integer, primary_key=True, index=True)
    valor_aproximado = Column(DECIMAL(10,2))
    fecha_cancelacion = Column(Date)
    dias_repeticion = Column(String(7))
    estado = Column(Boolean, default=False)
    id_hogar_f = Column(Integer, ForeignKey("hogares.id_hogar"), nullable=False)
    
    hogar = relationship("Hogar", backref="mensualidades")

class GastoMiembro(Base):
    __tablename__ = "gastos_miembro"
    id_gasto = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(50))
    descripcion = Column(String(250))
    valor_aproximado = Column(DECIMAL(10,2))
    dia_registro = Column(TIMESTAMP, default=datetime.utcnow)
    id_miembro_f = Column(Integer, ForeignKey("miembros.id_miembro"))
    
    miembro = relationship("Miembro", backref="gastos")

class ClasificacionIngrediente(Base):
    __tablename__ = "clasificacion_ingredientes"
    id_clasificacion = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)

class UnidadMedida(Base):
    __tablename__ = "unidades_medida"
    id_unidad = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(30), unique=True, nullable=False)
    abreviatura = Column(String(10))

class TipoIngrediente(Base):
    __tablename__ = "tipos_ingredientes"
    id_tipo_ingrediente = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    id_clasificacion = Column(Integer, ForeignKey("clasificacion_ingredientes.id_clasificacion"))
    id_unidad_base = Column(Integer, ForeignKey("unidades_medida.id_unidad"))
    caducidad_estandar_dias = Column(Integer)
    cantidad_minima_aviso = Column(Float, default=0.0)
    
    clasificacion = relationship("ClasificacionIngrediente")
    unidad_base = relationship("UnidadMedida")

class StockIngrediente(Base):
    __tablename__ = "stock_ingredientes"
    id_stock = Column(Integer, primary_key=True, index=True)
    id_hogar = Column(Integer, ForeignKey("hogares.id_hogar"), nullable=False)
    id_tipo_ingrediente = Column(Integer, ForeignKey("tipos_ingredientes.id_tipo_ingrediente"), nullable=False)
    cantidad = Column(Float, nullable=False, default=0.0)
    id_unidad = Column(Integer, ForeignKey("unidades_medida.id_unidad"))
    fecha_caducidad = Column(Date)
    fecha_registro = Column(TIMESTAMP, default=datetime.utcnow)
    
    hogar = relationship("Hogar")
    tipo_ingrediente = relationship("TipoIngrediente")
    unidad = relationship("UnidadMedida")

class HistorialConsumo(Base):
    __tablename__ = "historial_consumo"
    id_consumo = Column(Integer, primary_key=True, index=True)
    id_hogar = Column(Integer, ForeignKey("hogares.id_hogar"), nullable=False)
    id_tipo_ingrediente = Column(Integer, ForeignKey("tipos_ingredientes.id_tipo_ingrediente"), nullable=False)
    cantidad_consumida = Column(Float, nullable=False)
    id_unidad = Column(Integer, ForeignKey("unidades_medida.id_unidad"), nullable=False)
    fecha_consumo = Column(Date, nullable=False)
    
    hogar = relationship("Hogar")
    tipo_ingrediente = relationship("TipoIngrediente")
    unidad = relationship("UnidadMedida")