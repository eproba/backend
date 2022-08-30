from apps.blog.models import Post
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import BadHeaderError, send_mail
from django.http import HttpResponse
from django.shortcuts import redirect, render, reverse
from django.views import generic

try:
    import uwsgi
except ImportError:
    uwsgi = None

from .forms import ContactForm, IssueContactForm


def handler404(request, exception):
    return render(request, "errors/404.html", status=404)


def handler500(request):
    return render(request, "errors/500.html", status=500)


class FrontPageView(generic.ListView):
    template_name = "core/frontpage.html"

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Post.objects.filter(status=1, minimum_function=0).order_by(
                "-created_on"
            )

        return Post.objects.filter(
            status=1, minimum_function__lte=self.request.user.scout.function
        ).order_by("-created_on")


def contactView(request):
    if request.method == "GET":
        form = ContactForm()
    else:
        form = ContactForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data["subject"]
            from_email = form.cleaned_data["from_email"]
            message = form.cleaned_data["message"]
            try:
                send_mail(
                    f"{from_email}: {subject}",
                    message,
                    None,
                    ["eproba.zhr@gmail.com"],
                )
            except BadHeaderError:
                return HttpResponse("Invalid header found.")
            messages.add_message(request, messages.INFO, "Wiadomość została wysłana.")
            return redirect(reverse("frontpage"))
    return render(request, "sites/contact/email.html", {"form": form})


def IssueContactView(request):
    if request.method == "GET":
        form = IssueContactForm()
    else:
        form = IssueContactForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data["subject"]
            from_email = form.cleaned_data["from_email"]
            message = form.cleaned_data["message"]
            try:
                send_mail(
                    f"{from_email}: {subject}",
                    message,
                    None,
                    ["eproba.zhr@gmail.com"],
                )
            except BadHeaderError:
                return HttpResponse("Invalid header found.")
            messages.add_message(
                request,
                messages.INFO,
                f"Dziękujemy za zgłoszenie błędu, postaramy się rozwiązać go najszybciej jak to możliwe. Jeśli będziemy potrzebowali więcej informacji skontaktujemy się z tobą poprzez email {from_email}.",
            )
            return redirect(reverse("frontpage"))
    return render(request, "sites/contact/email-issue.html", {"form": form})


def fcm_sw(request):
    return render(
        request, "firebase-messaging-sw.js", content_type="application/javascript"
    )


@login_required
def reload_web_app(request):
    if request.user.is_superuser:
        if uwsgi:
            uwsgi.reload()
            messages.add_message(
                request, messages.INFO, "Aplikacja została ponownie uruchomiona."
            )
        else:
            messages.add_message(
                request,
                messages.WARNING,
                "Restart aplikacji nie jest dostępny na tej platformie.",
            )
        return redirect(reverse("frontpage"))
    return HttpResponse("Unathorized", status=401)
