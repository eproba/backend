from apps.users.utils import min_function, patrol_required
from django.shortcuts import render

from ..models import Worksheet


@patrol_required
@min_function(2)
def templates(request):
    worksheets = []
    if request.user.is_authenticated:
        worksheets = Worksheet.objects.filter(
            is_template=True,
            user__patrol__team=request.user.patrol.team,
            deleted=False,
        )

    return render(
        request,
        "worksheets/templates.html",
        {"user": request.user, "worksheets_list": worksheets},
    )
