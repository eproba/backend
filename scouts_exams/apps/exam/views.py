from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic


from .models import Exam

class ExamView(generic.ListView):
    template_name = 'exam/exam.html'
    context_object_name = 'exams_list'

    def get_queryset(self):
        """Return the last five published questions."""
        return Exam.objects.all()

def view_exams(request):
    user=request.user
    return render(
        request,
        "exam/exam.html",
        {"user": user, "exams_list": Exam.objects.filter(scout=user.id)},
    )