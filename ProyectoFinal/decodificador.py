from jose import jwt, JWTError
import os

# Configuración: asegúrate de que coincida con tu backend
SECRET_KEY = os.getenv("SECRET_KEY", "tu_clave_secreta_muy_larga_y_aleatoria")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# Tu token (access o refresh)
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjEsImV4cCI6MTc3NTI4MDc2OSwidHlwZSI6ImFjY2VzcyJ9.hSKEESXEaqt-vpn1eOba6oB1qKeMooPjcy97XsginiM"  # pega aquí el token

try:
    # Decodificar el token
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    print("Payload decodificado:", payload)

    # Validaciones adicionales
    sub = payload.get("sub")
    tipo = payload.get("type")
    exp = payload.get("exp")

    if not sub:
        print("❌ El token no contiene 'sub'")
    else:
        print(f"✅ sub (id_usuario): {sub}")

    if tipo != "access":
        print(f"⚠️ Este token es de tipo '{tipo}', no 'access'")
    else:
        print("✅ Token de tipo access")

    print(f"⏰ exp (timestamp): {exp}")

except JWTError as e:
    print("❌ Error al decodificar el token:", str(e))
