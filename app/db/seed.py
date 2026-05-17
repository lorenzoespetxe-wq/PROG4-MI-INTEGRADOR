from sqlmodel import Session, select
from app.core.database import engine
from app.core.security import hash_password

# Carga todos los modelos en el registry para resolver las forward references (strings) en las relaciones
import app.db.registry

from app.modules.usuarios.model import Rol, Usuario, UsuarioRol
from app.modules.pedidos.model import EstadoPedido, FormaPago
from app.modules.unidades.model import UnidadMedida


def seed_roles(session: Session) -> None:
    roles_data = [
        {
            "codigo": "ADMIN",
            "nombre": "Administrador",
            "descripcion": "Acceso total al sistema",
        },
        {
            "codigo": "STOCK",
            "nombre": "Gestor de Stock",
            "descripcion": "Gestión de inventario y productos",
        },
        {
            "codigo": "PEDIDOS",
            "nombre": "Gestor de Pedidos",
            "descripcion": "Gestión y seguimiento de pedidos",
        },
        {
            "codigo": "CLIENT",
            "nombre": "Cliente",
            "descripcion": "Usuario estándar de la plataforma",
        },
    ]
    for data in roles_data:
        if not session.exec(select(Rol).where(Rol.codigo == data["codigo"])).first():
            session.add(Rol(**data))


def seed_estados_pedido(session: Session) -> None:
    estados_data = [
        {
            "codigo": "PENDIENTE",
            "descripcion": "Pedido creado, esperando confirmación",
            "orden": 1,
            "es_terminal": False,
        },
        {
            "codigo": "CONFIRMADO",
            "descripcion": "Pedido confirmado y en cola",
            "orden": 2,
            "es_terminal": False,
        },
        {
            "codigo": "EN_PREP",
            "descripcion": "Pedido en preparación",
            "orden": 3,
            "es_terminal": False,
        },
        {
            "codigo": "EN_CAMINO",
            "descripcion": "Pedido en camino al cliente",
            "orden": 4,
            "es_terminal": False,
        },
        {
            "codigo": "ENTREGADO",
            "descripcion": "Pedido entregado exitosamente",
            "orden": 5,
            "es_terminal": True,
        },
        {
            "codigo": "CANCELADO",
            "descripcion": "Pedido cancelado",
            "orden": 6,
            "es_terminal": True,
        },
    ]
    for data in estados_data:
        if not session.exec(
            select(EstadoPedido).where(EstadoPedido.codigo == data["codigo"])
        ).first():
            session.add(EstadoPedido(**data))


def seed_formas_pago(session: Session) -> None:
    formas_data = [
        {"codigo": "MERCADOPAGO", "descripcion": "MercadoPago", "habilitado": True},
        {
            "codigo": "EFECTIVO",
            "descripcion": "Efectivo al recibir",
            "habilitado": True,
        },
        {
            "codigo": "TRANSFERENCIA",
            "descripcion": "Transferencia bancaria",
            "habilitado": True,
        },
    ]
    for data in formas_data:
        if not session.exec(
            select(FormaPago).where(FormaPago.codigo == data["codigo"])
        ).first():
            session.add(FormaPago(**data))


def seed_unidades_medida(session: Session) -> None:
    unidades_data = [
        {"nombre": "Kilogramo", "simbolo": "kg", "tipo": "masa"},
        {"nombre": "Gramo", "simbolo": "g", "tipo": "masa"},
        {"nombre": "Litro", "simbolo": "L", "tipo": "volumen"},
        {"nombre": "Mililitro", "simbolo": "ml", "tipo": "volumen"},
        {"nombre": "Unidad", "simbolo": "u", "tipo": "unidad"},
        {"nombre": "Porción", "simbolo": "por", "tipo": "unidad"},
    ]
    for data in unidades_data:
        if not session.exec(
            select(UnidadMedida).where(UnidadMedida.nombre == data["nombre"])
        ).first():
            session.add(UnidadMedida(**data))


def seed_admin_user(session: Session) -> None:
    admin_email = "admin@foodstore.com"
    admin = session.exec(select(Usuario).where(Usuario.email == admin_email)).first()

    if not admin:
        admin = Usuario(
            nombre="Admin",
            apellido="Sistema",
            email=admin_email,
            password_hash=hash_password("Admin1234!"),
            activo=True,
        )
        session.add(admin)
        session.flush()

        usuario_rol = UsuarioRol(
            usuario_id=admin.id, rol_codigo="ADMIN", asignado_por_id=None
        )
        session.add(usuario_rol)


def main() -> None:
    print("Iniciando carga de datos semilla...")
    with Session(engine) as session:
        seed_roles(session)
        seed_estados_pedido(session)
        seed_formas_pago(session)
        seed_unidades_medida(session)
        session.flush()

        seed_admin_user(session)

        session.commit()
    print("Carga de datos semilla completada exitosamente.")


if __name__ == "__main__":
    main()
