from apps.exam.models import Exam
from apps.exam.serializers import ExamSerializer
from apps.users.models import User
from apps.users.serializers import UserSerializer
from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope
from rest_framework import generics, permissions, viewsets


class UserList(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAdminUser, TokenHasReadWriteScope]
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetails(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAdminUser, TokenHasReadWriteScope]
    queryset = User.objects.all()
    serializer_class = UserSerializer


class ExamList(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser]
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer


class UserExamList(viewsets.ModelViewSet):
    serializer_class = ExamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Exam.objects.filter(scout__user__id=user.id)


class ExamDetails(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAdminUser]
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer


class UserExamDetails(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated, TokenHasReadWriteScope]
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer

    def get_queryset(self):
        user = self.request.user
        return Exam.objects.filter(scout__user__id=user.id)


class UserInfo(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return User.objects.filter(id=user.id)
