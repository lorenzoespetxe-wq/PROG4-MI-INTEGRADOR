# app/modules/ingredientes/service.py
import math
from app.core.unit_of_work import UnitOfWork
from app.core.exceptions import http_error, NOT_FOUND, ALREADY_EXISTS
from app.modules.ingredientes.model import Ingrediente
from app.modules.ingredientes.schemas import (
    IngredienteCreate,
    IngredienteUpdate,
    IngredienteRead,
    PaginatedIngredientes,
)
from app.modules.ingredientes.repository import IngredienteRepository


class IngredienteService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def _map_to_read(self, ingrediente: Ingrediente) -> IngredienteRead:
        return IngredienteRead.model_validate(ingrediente)

    def _get_active_ingrediente(
        self, repo: IngredienteRepository, id: int
    ) -> Ingrediente:
        ingrediente = repo.get_by_id(id)
        if not ingrediente or ingrediente.deleted_at is not None:
            raise http_error(404, "Ingrediente no encontrado", NOT_FOUND)
        return ingrediente

    def crear(self, data: IngredienteCreate) -> IngredienteRead:
        with self.uow:
            repo = IngredienteRepository(self.uow.session)

            if repo.get_by_nombre(data.nombre):
                raise http_error(
                    409, "Ya existe un ingrediente con este nombre", ALREADY_EXISTS
                )

            nuevo_ingrediente = Ingrediente(
                nombre=data.nombre,
                es_alergeno=data.es_alergeno,
                descripcion=data.descripcion,
            )
            self.uow.session.add(nuevo_ingrediente)
            self.uow.session.flush()
            self.uow.session.refresh(nuevo_ingrediente)

            return self._map_to_read(nuevo_ingrediente)

    def listar(
        self, page: int, size: int, solo_alergenos: bool
    ) -> PaginatedIngredientes:
        with self.uow:
            repo = IngredienteRepository(self.uow.session)
            skip = (page - 1) * size

            items = repo.list_activos(
                skip=skip, limit=size, solo_alergenos=solo_alergenos
            )
            total = repo.count_activos(solo_alergenos=solo_alergenos)
            pages = math.ceil(total / size) if size > 0 else 0

            return PaginatedIngredientes(
                items=[self._map_to_read(i) for i in items],
                total=total,
                page=page,
                size=size,
                pages=pages,
            )

    def get_ingrediente(self, id: int) -> IngredienteRead:
        with self.uow:
            repo = IngredienteRepository(self.uow.session)
            ingrediente = self._get_active_ingrediente(repo, id)
            return self._map_to_read(ingrediente)

    def actualizar(self, id: int, data: IngredienteUpdate) -> IngredienteRead:
        with self.uow:
            repo = IngredienteRepository(self.uow.session)
            ingrediente = self._get_active_ingrediente(repo, id)

            update_data = data.model_dump(exclude_unset=True)

            if "nombre" in update_data and update_data["nombre"] != ingrediente.nombre:
                if repo.get_by_nombre(update_data["nombre"]):
                    raise http_error(
                        409, "Ya existe un ingrediente con este nombre", ALREADY_EXISTS
                    )

            ingrediente = repo.update(ingrediente, update_data)
            return self._map_to_read(ingrediente)

    def eliminar(self, id: int) -> None:
        with self.uow:
            repo = IngredienteRepository(self.uow.session)
            ingrediente = self._get_active_ingrediente(repo, id)

            if repo.esta_en_uso(id):
                raise http_error(
                    409,
                    "El ingrediente está asociado a productos activos",
                    ALREADY_EXISTS,
                )

            repo.soft_delete(ingrediente)
