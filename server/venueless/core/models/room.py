import uuid

from django.contrib.postgres.fields import JSONField
from django.db import models


class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    world = models.ForeignKey(
        to="core.World", related_name="rooms", on_delete=models.PROTECT
    )
    permission_config = JSONField(null=True, blank=True)
    module_config = JSONField(null=True, blank=True)
    name = models.CharField(max_length=300)
    description = models.TextField(null=True, blank=True)
    picture = models.FileField(null=True, blank=True)

    import_id = models.CharField(max_length=100, null=True, blank=True)