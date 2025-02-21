import uuid

from django.db import models
from django.db.models import UUIDField
from django.urls import reverse
from tinymce.models import HTMLField
from treebeard.mp_tree import MP_Node

from ..teams.models import District, OrganizationChoice, Patrol, Team
from ..users.models import User

MAX_DEPTH = 6


class Folder(MP_Node):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    visible = models.BooleanField(default=True)

    inherit_permissions = models.BooleanField(default=True)
    for_all = models.BooleanField(default=False)
    organization = models.IntegerField(
        choices=OrganizationChoice.choices, null=True, blank=True
    )
    district = models.ForeignKey(
        District, null=True, blank=True, on_delete=models.CASCADE
    )
    team = models.ForeignKey(Team, null=True, blank=True, on_delete=models.CASCADE)
    patrol = models.ForeignKey(Patrol, null=True, blank=True, on_delete=models.CASCADE)

    node_order_by = ["name"]  # Automatically orders nodes alphabetically

    class Meta:
        verbose_name = "Folder"
        verbose_name_plural = "Folders"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("wiki:folder", kwargs={"pk": self.pk})

    # Optimized permission check
    def can_view(self, user: User, for_list=False):
        if self.for_all or user.is_superuser or self.owner == user:
            return not for_list

        user_patrol = getattr(user, "patrol", None)
        user_team = getattr(user_patrol, "team", None) if user_patrol else None

        # Check this folder
        if (
            (
                self.organization
                and user_team
                and user_team.organization == self.organization
            )
            or (self.district and user_team and user_team.district == self.district)
            or (self.team and user_team and user_team == self.team)
            or (self.patrol and user_patrol and user_patrol == self.patrol)
        ):
            return True

        # Check all its parent folders
        if self.inherit_permissions:
            for folder in self.get_ancestors():
                if (
                    (
                        folder.organization
                        and user_team
                        and user_team.organization == folder.organization
                    )
                    or (
                        folder.district
                        and user_team
                        and user_team.district == folder.district
                    )
                    or (folder.team and user_team and user_team == folder.team)
                    or (folder.patrol and user_patrol and user_patrol == folder.patrol)
                ):
                    return True

        return False

    # Optimized edit permission check
    def can_edit(self, user: User):
        if user.is_superuser or self.owner == user:
            return True

        # Check the entire hierarchy for edit permission
        for folder in self.get_ancestors():
            if folder.owner == user:
                return True

        return False

    def get_pages(self):
        return self.pages.all()

    def get_content(self):
        return self.get_children(), self.get_pages()

    def get_content_count(self):
        return self.get_children().count(), self.get_pages().count()

    def get_content_count_combined(self):
        return self.get_children().count() + self.get_pages().count()

    def is_empty(self):
        return not self.get_content_count_combined()

    def get_path(self):
        return self.get_ancestors()


class Page(models.Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    content = HTMLField()
    folder = models.ForeignKey(
        Folder, on_delete=models.CASCADE, related_name="pages", null=True, blank=True
    )
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    visible = models.BooleanField(default=True)

    inherit_permissions = models.BooleanField(default=True)
    for_all = models.BooleanField(default=False)
    organization = models.IntegerField(
        choices=OrganizationChoice.choices, null=True, blank=True
    )
    district = models.ForeignKey(
        District, null=True, blank=True, on_delete=models.CASCADE
    )
    team = models.ForeignKey(Team, null=True, blank=True, on_delete=models.CASCADE)
    patrol = models.ForeignKey(Patrol, null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Page"
        verbose_name_plural = "Pages"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("wiki:page", kwargs={"pk": self.pk})

    def can_view(self, user: User):
        if self.for_all or user.is_superuser or self.owner == user:
            return True

        user_patrol = getattr(user, "patrol", None)
        user_team = getattr(user_patrol, "team", None) if user_patrol else None

        return (
            (
                self.organization
                and user_team
                and user_team.organization == self.organization
            )
            or (self.district and user_team and user_team.district == self.district)
            or (self.team and user_team and user_team == self.team)
            or (self.patrol and user_patrol and user_patrol == self.patrol)
            or (self.folder and self.inherit_permissions and self.folder.can_view(user))
        )

    def can_edit(self, user: User):
        if user.is_superuser or self.owner == user:
            return True
        if self.folder:
            return self.folder.can_edit(user)
        return False
