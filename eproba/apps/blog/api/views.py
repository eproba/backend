from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from ..models import Post
from .serializers import PostSerializer


class PostViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for blog posts
    """

    serializer_class = PostSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        queryset = Post.objects.filter(status=1)

        if self.request.user.is_authenticated:
            queryset.filter(
                minimum_function__lte=self.request.user.function,
            )
        else:
            queryset = queryset.filter(authorized_only=False, minimum_function=0)

        if self.action == "list":
            queryset = queryset.filter(hidden=False)

        return queryset
