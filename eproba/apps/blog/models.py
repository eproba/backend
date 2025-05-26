import uuid

from django.db import models
from django.db.models import UUIDField
from django.urls import reverse

from ..users.models import User

STATUS = ((0, "draft"), (1, "published"), (2, "archived"))


class Post(models.Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="blog_posts"
    )
    updated_on = models.DateTimeField(auto_now=True)
    content = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(choices=STATUS, default=0)
    authorized_only = models.BooleanField(
        default=False,
        help_text="Czy post jest dostępny tylko dla zalogowanych użytkowników?",
    )
    minimum_function = models.IntegerField(choices=User.FUNCTION_CHOICES, default=0)
    pinned = models.BooleanField(
        default=False, help_text="Czy post jest przypięty na stronie głównej?"
    )
    priority = models.IntegerField(
        default=0,
        help_text="Priorytet postu (wyższy priorytet = wyższa pozycja na liście)",
    )
    hidden = models.BooleanField(
        default=False,
        help_text="Czy post jest ukryty - nie będzie wyświetlany na liście postów.",
    )

    class Meta:
        ordering = ["-created_on"]

    def __str__(self) -> str:
        return str(self.title)

    def get_absolute_url(self):
        return reverse("blog:post_detail", kwargs={"slug": str(self.slug)})
