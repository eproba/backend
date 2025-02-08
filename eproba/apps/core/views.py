from apps.blog.models import Post
from constance import config
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import BadHeaderError, send_mail
from django.http import HttpResponse
from django.shortcuts import redirect, render, reverse
from django.views import generic

from .forms import ContactForm


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
            status=1, minimum_function__lte=self.request.user.function
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
                    ["eproba@zhr.pl"],
                )
            except BadHeaderError:
                return HttpResponse("Invalid header found.")
            messages.info(request, "Wiadomość została wysłana.")
            return redirect(reverse("frontpage"))
    return render(request, "sites/contact/email.html", {"form": form})


def fcm_sw(request):
    return render(
        request, "firebase-messaging-sw.js", content_type="application/javascript"
    )


@login_required
def site_management(request):
    if not request.user.is_superuser:
        return redirect(reverse("frontpage"))
    if request.method == "POST":
        config.ADS_WEB = bool(request.POST.get("ads_web", False))
        config.ADS_MOBILE = bool(request.POST.get("ads_mobile", False))
        config.WEB_MAINTENANCE_MODE = bool(request.POST.get("maintenance_web", False))
        config.API_MAINTENANCE_MODE = bool(request.POST.get("maintenance_api", False))
        config.MINIMUM_APP_VERSION = request.POST.get("min_app_version", "0")
        config.REQUIRE_EMAIL_VERIFICATION = bool(
            request.POST.get("require_email_verification", False)
        )
        return redirect(reverse("site_management"))
    return render(request, "sites/site_management.html")
