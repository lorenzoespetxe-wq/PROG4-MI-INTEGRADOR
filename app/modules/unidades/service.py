# app/modules/unidades/service.py
from app.core.unit_of_work import UnitOfWork
from app.core.exceptions import http_error, NOT_FOUND, ALREADY_EXISTS
from app.modules.unidades.model import UnidadMedida
from app.modules.unidades.schemas import (
    UnidadMedidaCreate,
    UnidadMedidaUpdate,
    UnidadMedidaRead,
)
from app.modules.unidades.repository import UnidadMedidaRepository


class UnidadMedidaService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def _map_to_read(self, unidad: UnidadMedida) -> UnidadMedidaRead:
        return UnidadMedidaRead.model_validate(unidad)

    def _get_unidad(self, repo: UnidadMedidaRepository, id: int) -> UnidadMedida:
        unidad = repo.get_by_id(id)
        if not unidad:
            raise http_error(404, "Unidad de medida no encontrada", NOT_FOUND)
        return unidad

    def crear(self, data: UnidadMedidaCreate) -> UnidadMedidaRead:
        with self.uow:
            repo = UnidadMedidaRepository(self.uow.session)

            if repo.get_by_nombre(data.nombre):
                raise http_error(
                    409,
                    "Ya existe una unidad de medida con este nombre",
                    ALREADY_EXISTS,
                )

            if repo.get_by_simbolo(data.simbolo):
                raise http_error(
                    409,
                    "Ya existe una unidad de medida con este símbolo",
                    ALREADY_EXISTS,
                )

            nueva_unidad = UnidadMedida(
                nombre=data.nombre, simbolo=data.simbolo, tipo=data.tipo
            )
            self.uow.session.add(nueva_unidad)
            self.uow.session.flush()
            self.uow.session.refresh(nueva_unidad)
            return self._map_to_read(nueva_unidad)

    def listar(self, page: int = 1, size: int = 100) -> list[UnidadMedidaRead]:
        with self.uow:
            repo = UnidadMedidaRepository(self.uow.session)
            skip = (page - 1) * size
            unidades = repo.get_todas(skip=skip, limit=size)
            return [self._map_to_read(u) for u in unidades]

    def obtener_por_id(self, id: int) -> UnidadMedidaRead:
        with self.uow:
            repo = UnidadMedidaRepository(self.uow.session)
            unidad = self._get_unidad(repo, id)
            return self._map_to_read(unidad)

    def actualizar(self, id: int, data: UnidadMedidaUpdate) -> UnidadMedidaRead:
        with self.uow:
            repo = UnidadMedidaRepository(self.uow.session)
            unidad = self._get_unidad(repo, id)

            update_data = data.model_dump(exclude_unset=True)

            if "nombre" in update_data and update_data["nombre"] != unidad.nombre:
                if repo.get_by_nombre(update_data["nombre"]):
                    raise http_error(
                        409,
                        "Ya existe una unidad de medida con este nombre",
                        ALREADY_EXISTS,
                    )

            if "simbolo" in update_data and update_data["simbolo"] != unidad.simbolo:
                if repo.get_by_simbolo(update_data["simbolo"]):
                    raise http_error(
                        409,
                        "Ya existe una unidad de medida con este símbolo",
                        ALREADY_EXISTS,
                    )

            unidad = repo.update(unidad, update_data)
            return self._map_to_read(unidad)

    def eliminar(self, id: int) -> None:
        with self.uow:
            repo = UnidadMedidaRepository(self.uow.session)
            unidad = self._get_unidad(repo, id)

            # Validación de integridad referencial basada en relaciones cargadas
            if len(unidad.productos) > 0 or len(unidad.producto_ingredientes) > 0:
                raise http_error(
                    409,
                    "No se puede eliminar la unidad porque está siendo utilizada por productos o ingredientes",
                    ALREADY_EXISTS,
                )

            # No posee SoftDeleteMixin según el modelo proporcionado, se realiza un hard delete controlado
            self.uow.session.delete(unidad)
            self.uow.session.flush()
