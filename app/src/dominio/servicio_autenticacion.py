from persistencia.repositorio import IRepositorioDatos

from dominio.models_usuario import Usuario
from dominio.seguridad import encriptar_contrasena


class ServicioAutenticacion:
    """Gestiona el registro e inicio de sesión con validaciones sencillas."""

    def __init__(self, repositorio: IRepositorioDatos):
        self.repo = repositorio

    def registrar_usuario(
        self, email: str, apodo: str, contrasena: str
    ) -> tuple[bool, str, Usuario | None]:
        # 1. Validación de Alias (Máximo 8 caracteres)
        apodo = apodo.strip()
        if not apodo or len(apodo) > 8:
            return False, "El alias debe tener entre 1 y 8 caracteres.", None

        # 2. Validación de Contraseña (Mínimo 4, Máximo 8 caracteres)
        if len(contrasena) < 4 or len(contrasena) > 8:
            return False, "La contraseña debe tener entre 4 y 8 caracteres.", None

        # 3. Validación de Email básico
        if "@" not in email or "." not in email:
            return False, "El formato de correo electrónico no es válido.", None

        # 4. Verificar si el alias ya existe
        if self.repo.obtener_usuario_por_apodo(apodo):
            return False, f"El alias '{apodo}' ya está registrado. Elige otro.", None

        # 5. Hashear contraseña y crear entidad
        clave_hash = encriptar_contrasena(contrasena)
        nuevo_usuario = Usuario(email=email, apodo=apodo, clave_hash=clave_hash)

        # 6. Persistir
        self.repo.guardar_usuario(nuevo_usuario)
        return True, "¡Registro exitoso!", nuevo_usuario

    def iniciar_sesion(
        self, apodo: str, contrasena: str
    ) -> tuple[bool, str, Usuario | None]:
        apodo = apodo.strip()
        if len(apodo) > 8:
            return False, "El alias no puede superar los 8 caracteres.", None

        usuario = self.repo.obtener_usuario_por_apodo(apodo)
        if not usuario:
            return False, "Alias o contraseña incorrectos.", None

        # Comparar hash enviado vs hash almacenado
        hash_ingresado = encriptar_contrasena(contrasena)
        if usuario.clave_hash != hash_ingresado:
            return False, "Alias o contraseña incorrectos.", None

        return True, f"¡Bienvenido de nuevo, {usuario.apodo}!", usuario
