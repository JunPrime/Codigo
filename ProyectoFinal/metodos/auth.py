from dotenv import load_dotenv
load_dotenv()
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import os

from database import get_db
from modelos.modelos import Usuario, RefreshToken  # Ajusta según tu estructura
from esquemas.schemas import UsuarioCreate, UsuarioUpdate, UsuarioSchema, Token, PasswordVerify


SECRET_KEY = os.getenv("SECRET_KEY", "tu_clave_secreta_muy_larga_y_aleatoria")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 14))

if SECRET_KEY is None or ALGORITHM is None:
    raise ValueError("SECRET_KEY y ALGORITHM deben definirse en el archivo .env")

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")



router = APIRouter(prefix="/auth", tags=["autenticación"])


# ----- Helper functions -----
def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(db, correo, password):
    usuario = db.query(Usuario).filter(Usuario.correo == correo).first()
    if not usuario or not verify_password(password, usuario.contraseña):
        return False
    return usuario

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    # Convertir sub a string
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire, "type": "refresh"})
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_refresh_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        id_usuario = payload.get("sub")
        if id_usuario is None:
            return None
        # Opcional: verificar en BD si fue revocado
        token_db = db.query(RefreshToken).filter(
            RefreshToken.token == token,
            RefreshToken.revoked == False,
            RefreshToken.expires_at > datetime.utcnow()
        ).first()
        if not token_db:
            return None
        return id_usuario
    except JWTError:
        return None

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        tipo = payload.get("type")

        # Validar que exista sub y que sea de tipo access
        if sub is None or tipo != "access":
            raise credentials_exception

        # Convertir sub (string) a entero para usarlo como id_usuario
        try:
            id_usuario = int(sub)
        except ValueError:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Buscar el usuario en la BD
    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario:
        raise credentials_exception
    return usuario



# ----- Endpoints -----
@router.post("/register", response_model=UsuarioSchema, status_code=201)
def register(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    if db.query(Usuario).filter(Usuario.correo == usuario.correo).first():
        raise HTTPException(400, "El correo ya está registrado")
    hashed = get_password_hash(usuario.contraseña)
    db_usuario = Usuario(nombre=usuario.nombre, correo=usuario.correo, contraseña=hashed)
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = authenticate_user(db, form_data.username, form_data.password)
    if not usuario:
        raise HTTPException(401, "Correo o contraseña incorrectos")
    
    access_token = create_access_token(data={"sub": usuario.id_usuario})
    refresh_token = create_refresh_token(data={"sub": usuario.id_usuario})
    
    # Guardar refresh token en BD (opcional, para revocación)
    new_refresh = RefreshToken(
        token=refresh_token,
        id_usuario=usuario.id_usuario,
        expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(new_refresh)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/refresh", response_model=Token)
def refresh(refresh_token: str = Body(..., embed=True), db: Session = Depends(get_db)):
    id_usuario = verify_refresh_token(refresh_token, db)
    if not id_usuario:
        raise HTTPException(401, "Refresh token inválido o expirado")
    
    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(401, "Usuario no encontrado")
    
    new_access = create_access_token(data={"sub": usuario.id_usuario})
    # Opcional: rotar refresh token (generar uno nuevo y revocar el anterior)
    new_refresh = create_refresh_token(data={"sub": usuario.id_usuario})
    # return { "access_token": new_access, "refresh_token": new_refresh, ... }
    
    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/verify-password")
def verify_password_endpoint(
    data: PasswordVerify,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(data.password, current_user.contraseña):
        raise HTTPException(401, "Contraseña incorrecta")
    return {"message": "Contraseña correcta"}

@router.get("/me", response_model=UsuarioSchema)
def me(current_user: Usuario = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UsuarioSchema)
def update_user(
    update_data: UsuarioUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verificar contraseña actual
    if not verify_password(update_data.current_password, current_user.contraseña):
        raise HTTPException(400, "Contraseña actual incorrecta")
    
    if update_data.nombre:
        current_user.nombre = update_data.nombre
    if update_data.correo:
        if update_data.correo != current_user.correo:
            if db.query(Usuario).filter(Usuario.correo == update_data.correo).first():
                raise HTTPException(400, "Correo ya en uso")
        current_user.correo = update_data.correo
    if update_data.contraseña:
        current_user.contraseña = get_password_hash(update_data.contraseña)
    
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/logout")
def logout(refresh_token: str = Body(..., embed=True), db: Session = Depends(get_db)):
    # Revocar refresh token en BD
    token_db = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
    if token_db:
        token_db.revoked = True
        db.commit()
    return {"message": "Sesión cerrada correctamente"}