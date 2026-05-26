from django.db import models
from django.utils import timezone


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class SoftDeleteMixin(models.Model):
    """
    Mixin que implementa eliminación lógica (soft delete).

    Los registros marcados con is_deleted=True no aparecen en las consultas
    normales (objects), pero siguen existiendo en la BD y son accesibles
    via all_objects para administradores o auditoría.
    """

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    def delete(self, using=None, keep_parents=False, deleted_by=None):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if deleted_by:
            self.deleted_by = deleted_by
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by_id"])

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by_id"])

    class Meta:
        abstract = True
