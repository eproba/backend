from apps.users.utils import min_function, patrol_required
from django.db.models import Q
from django.shortcuts import render

from ..models import TemplateWorksheet


@patrol_required
@min_function(2)
def templates(request):
    worksheet_templates = []
    if request.user.is_authenticated:
        worksheet_templates = TemplateWorksheet.objects.filter(
            Q(team=request.user.patrol.team)
            | Q(team=None, organization=request.user.patrol.team.organization)
        )

    return render(
        request,
        "worksheets/templates.html",
        {"user": request.user, "worksheet_templates": worksheet_templates},
    )
