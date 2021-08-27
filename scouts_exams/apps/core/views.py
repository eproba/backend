from django.contrib import messages
from django.core.mail import BadHeaderError, send_mail
from django.http import HttpResponse
from django.shortcuts import redirect, render, reverse

from .forms import ContactForm, IssueContactForm


def handler500(request):
    return render(request, "sites/500.html", status=500)


def frontpage(request):
    return render(request, "core/frontpage.html")


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
                    ["antekczaplicki@gmail.com"],
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
                    ["antekczaplicki@gmail.com"],
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
