from channels.db import database_sync_to_async
from django.db.transaction import atomic

from venueless.core.models import (
    AuditLog,
    ContactRequest,
    Exhibitor,
    ExhibitorLink,
    ExhibitorSocialMediaLink,
    ExhibitorStaff,
    Room,
)
from venueless.core.services.user import get_user_by_id


def get_exhibitor_by_id(world_id, id):
    try:
        return Exhibitor.objects.get(id=id, world_id=world_id)
    except Exhibitor.DoesNotExist:
        return


def get_request_by_id(world_id, id):
    try:
        return ContactRequest.objects.get(id=id, exhibitor__world_id=world_id)
    except ContactRequest.DoesNotExist:
        return


def get_staff_by_id(exhibitor_id, user_id):
    try:
        return ExhibitorStaff.objects.get(exhibitor__id=exhibitor_id, user__id=user_id)
    except ExhibitorStaff.DoesNotExist:
        return


def get_or_create_social_media_link(link, exhibitor):
    obj, _ = ExhibitorSocialMediaLink.objects.get_or_create(
        exhibitor=exhibitor,
        display_text=link["display_text"],
        url=link["url"],
        defaults=dict(
            exhibitor=exhibitor,
            display_text=link["display_text"],
            url=link["url"],
        ),
    )
    return obj


def get_or_create_link(link, exhibitor):
    obj, _ = ExhibitorLink.objects.get_or_create(
        exhibitor=exhibitor,
        display_text=link["display_text"],
        url=link["url"],
        category=link["category"],
        defaults=dict(
            exhibitor=exhibitor,
            display_text=link["display_text"],
            url=link["url"],
            category=link["category"],
        ),
    )
    return obj


def get_or_create_staff(user, exhibitor):
    obj, _ = ExhibitorStaff.objects.get_or_create(
        exhibitor=exhibitor,
        user__id=user.id,
        defaults=dict(
            exhibitor=exhibitor,
            user=user,
        ),
    )
    return obj


def get_room_by_id(world_id, id):
    try:
        return Room.objects.get(id=id, world__id=world_id)
    except Room.DoesNotExist:
        return


class ExhibitionService:
    def __init__(self, world_id):
        self.world_id = world_id

    @database_sync_to_async
    def get_all_exhibitors(self):
        qs = Exhibitor.objects.filter(world__id=self.world_id).order_by("name")

        return [
            dict(
                id=str(e["id"]),
                name=e["name"],
            )
            for e in qs.values(
                "id",
                "name",
            )
        ]

    @database_sync_to_async
    def get_exhibitors(self, room_id):
        qs = (
            Exhibitor.objects.filter(world__id=self.world_id)
            .filter(room__id=room_id)
            .order_by("sorting_priority", "name")
        )

        return [
            dict(
                id=str(e["id"]),
                name=e["name"],
                tagline=e["tagline"],
                short_text=e["short_text"],
                logo=e["logo"],
                banner_list=e["banner_list"],
                size=e["size"],
                sorting_priority=e["sorting_priority"],
            )
            for e in qs.values(
                "id",
                "name",
                "tagline",
                "short_text",
                "banner_list",
                "logo",
                "size",
                "sorting_priority",
            )
        ]

    @database_sync_to_async
    def get_exhibitor(self, exhibitor_id):
        e = get_exhibitor_by_id(self.world_id, exhibitor_id)
        if not e:
            return None
        return e.serialize()

    @database_sync_to_async
    @atomic
    def delete(self, exhibitor_id, by_user):
        e = get_exhibitor_by_id(self.world_id, exhibitor_id)
        if not e:
            return None
        AuditLog.objects.create(
            world_id=self.world_id,
            user=by_user,
            type="exhibition.exhibitor.deleted",
            data={
                "object": exhibitor_id,
                "old": e.serialize(),
            },
        )
        return e.delete()

    @database_sync_to_async
    @atomic
    def patch(self, exhibitor, world, by_user):
        room = get_room_by_id(self.world_id, exhibitor["room_id"])
        if not room:
            return None

        if exhibitor["id"] == "":
            e = Exhibitor(
                room=room,
                world=world,
            )
            old = {}
        else:
            e = get_exhibitor_by_id(self.world_id, exhibitor["id"])
            if not e:
                return None
            old = e.serialize()

        for k in (
            "name",
            "tagline",
            "short_text",
            "text",
            "size",
            "sorting_priority",
            "logo",
            "banner_list",
            "banner_detail",
            "contact_enabled",
        ):
            if k in exhibitor:
                setattr(e, k, exhibitor[k])
        e.save()

        if "social_media_links" in exhibitor:
            social_media_links = []
            for link in exhibitor["social_media_links"]:
                social_media_links.append(get_or_create_social_media_link(link, e))
            for link in e.social_media_links.all():
                if link not in social_media_links:
                    link.delete()

        if "links" in exhibitor:
            links = []
            for link in exhibitor["links"]:
                links.append(get_or_create_link(link, e))
            for link in e.links.all():
                if link not in links:
                    link.delete()

        if "staff" in exhibitor:
            staff = []
            for user in exhibitor["staff"]:
                user = get_user_by_id(self.world_id, user["id"])
                staff.append(get_or_create_staff(user, e))
            for staff_member in e.staff.all():
                if staff_member not in staff:
                    staff_member.delete()

        new = e.serialize()
        AuditLog.objects.create(
            world_id=self.world_id,
            user=by_user,
            type="exhibition.exhibitor.updated",
            data={
                "object": str(e.id),
                "old": old,
                "new": new,
            },
        )

        return new

    @database_sync_to_async
    def contact(self, exhibitor_id, user):
        e = get_exhibitor_by_id(self.world_id, exhibitor_id)
        if not e:
            return None
        request = ContactRequest.objects.create(
            exhibitor=e,
            user=user,
        )
        return request.serialize()

    @database_sync_to_async
    def missed(self, contact_request_id):
        r = get_request_by_id(self.world_id, contact_request_id)
        if not r:
            return None
        if r.state == "answered":
            return None
        r.state = "missed"
        r.save(update_fields=["state"])
        return r.serialize()

    @database_sync_to_async
    def accept(self, contact_request_id, staff):
        r = get_request_by_id(self.world_id, contact_request_id)
        if not r:
            return None
        if r.state == "answered":
            return None
        r.state = "answered"
        r.answered_by = staff
        r.save(update_fields=["state", "answered_by"])
        return r.serialize()

    @database_sync_to_async
    @atomic
    def add_staff(self, exhibitor_id, user_id, by_user):
        e = get_exhibitor_by_id(self.world_id, exhibitor_id)
        if not e:
            return None
        u = get_user_by_id(self.world_id, user_id)
        if not u:
            return None
        try:
            s = ExhibitorStaff.objects.get(
                user=u,
                exhibitor=e,
            )
        except ExhibitorStaff.DoesNotExist:
            s = ExhibitorStaff.objects.create(
                user=u,
                exhibitor=e,
            )
        AuditLog.objects.create(
            world_id=self.world_id,
            user=by_user,
            type="exhibition.exhibitor.staff.added",
            data={
                "object": exhibitor_id,
                "staff": user_id,
            },
        )
        return s

    @database_sync_to_async
    @atomic
    def remove_staff(self, exhibitor_id, user_id, by_user):
        s = get_staff_by_id(exhibitor_id, user_id)
        if not s:
            return None
        AuditLog.objects.create(
            world_id=self.world_id,
            user=by_user,
            type="exhibition.exhibitor.staff.removed",
            data={
                "object": exhibitor_id,
                "staff": user_id,
            },
        )
        return s.delete()

    @database_sync_to_async
    def get_staff(self, exhibitor_id):
        e = get_exhibitor_by_id(self.world_id, exhibitor_id)
        if not e:
            return None
        return list(e.staff.values_list("user__id", flat=True))

    @database_sync_to_async
    def get_open_requests_from_user(self, user):
        return [
            cr.serialize()
            for cr in user.exhibitor_contact_requests.filter(state="open")
        ]

    @database_sync_to_async
    def get_exhibitions_staffed_by_user(self, user_id):
        exhibitors = Exhibitor.objects.filter(
            world__id=self.world_id,
            staff__user__id=user_id,
        )
        return [ex.serialize() for ex in exhibitors]

    def get_exhibition_data_for_user(self, user_id):
        exhibitors = Exhibitor.objects.filter(
            world__id=self.world_id,
            staff__user__id=user_id,
        )
        contact_requests = ContactRequest.objects.filter(exhibitor__in=exhibitors)
        return {
            "exhibitors": [ex.serialize_short() for ex in exhibitors],
            "contact_requests": [cr.serialize() for cr in contact_requests],
        }
