import datetime
from django.db import models
from django.utils import timezone
from ..users.models import Scout
from cryptography.fernet import Fernet
key = b'PsDHtsLu37lIQiHzmWO88Do9YpBIiy5STBSwV04HeCg='

def encrypt(message: bytes, key: bytes) -> bytes:
    return Fernet(key).encrypt(message)

def decrypt(token: bytes, key: bytes) -> bytes:
    return Fernet(key).decrypt(token)

class Exam(models.Model):
    scout = models.ForeignKey(
        Scout, on_delete=models.RESTRICT, null=True, default=None, related_name="scout", blank=True
    )
    name = models.CharField(max_length=200)
    def __str__(self):
        return self.name


class Task(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    task = models.CharField(max_length=200)
    is_done = models.BooleanField(default=False)
    approver = models.ForeignKey(
        Scout, on_delete=models.RESTRICT, null=True, default=None, related_name="approver", blank=True
    )
    approval_date = models.DateTimeField(auto_now=True)
    #key = models.CharField(max_length=200, blank=True, default=encrypt("task".encode(), key))
    def __str__(self):
        return self.task
    REQUIRED_FIELDS = ["exam", "task"]
