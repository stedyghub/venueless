import copy

from django.db import transaction

from stayseated.core.models import Channel, Room, World


@transaction.atomic
def import_config(data):
    data = copy.deepcopy(data)
    world_config = data.pop("world")
    world, _ = World.objects.get_or_create(id=world_config.pop("id"))
    world.title = world_config.pop("title")
    world.about = world_config.pop("about")
    world.config = world_config
    world.permission_config = data.pop("permissions")
    world.save()

    for room_config in data.pop("rooms"):
        room, _ = Room.objects.get_or_create(
            import_id=room_config.pop("id"),
            world=world,
            defaults={"name": room_config["name"]},
        )
        room.name = room_config.pop("name")
        room.description = room_config.pop("description")
        room_config.pop("picture")  # TODO import picure from path or http
        room.permission_config = room_config.pop("permissions", {})
        room.module_config = room_config.pop("modules")
        room.save()
        assert not room_config, f"Unused config data: {room_config}"

        for module in room.module_config:
            if module["type"] == "chat.native":
                Channel.objects.get_or_create(room=room, world=world)

    assert not data, f"Unused config data: {data}"
