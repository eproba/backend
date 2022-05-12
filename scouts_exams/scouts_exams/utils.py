from apps.exam.models import Exam, Task
from apps.exam.permissions import IsAllowedToManageExamOrReadOnlyForOwner
from apps.exam.serializers import ExamSerializer
from apps.users.models import User
from apps.users.serializers import UserSerializer
from rest_framework import generics, permissions, viewsets
from rest_framework.viewsets import ModelViewSet


class UserList(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAdminUser]
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetails(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAdminUser]
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


class ExamViewSet(ModelViewSet):
    permission_classes = [IsAllowedToManageExamOrReadOnlyForOwner]
    serializer_class = ExamSerializer

    def get_queryset(self):
        user = self.request.user
        if user.scout.function >= 5:
            return Exam.objects.all()
        elif user.scout.patrol.team and user.scout.function >= 2:
            return Exam.objects.filter(scout__patrol__team__id=user.scout.patrol.team.id)
        return Exam.objects.filter(scout__user__id=user.id)


class UserExamDetails(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
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
