from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Folder, Page


@login_required
def folder(request, folder_id=None):
    if folder_id:
        folder_obj = get_object_or_404(Folder, id=folder_id)
        folders = [
            _folder
            for _folder in folder_obj.get_children()
            if _folder.can_view(request.user)
        ]
        pages = [
            _page for _page in folder_obj.get_pages() if _page.can_view(request.user)
        ]
        path = folder_obj.get_ancestors()  # Get breadcrumb path
        return render(
            request,
            "wiki/index.html",
            {"folders": folders, "pages": pages, "path": path, "folder": folder_obj},
        )

    # Get root-level folders (those without a parent)
    folders = Folder.get_root_nodes().filter(
        Q(owner=request.user)
        | Q(for_all=True)
        | Q(team=request.user.patrol.team)
        | Q(patrol=request.user.patrol)
        | Q(organization=request.user.patrol.team.organization)
        | Q(district=request.user.patrol.team.district)
    )
    pages = Page.objects.filter(folder=None).filter(
        Q(owner=request.user)
        | Q(for_all=True)
        | Q(team=request.user.patrol.team)
        | Q(patrol=request.user.patrol)
        | Q(organization=request.user.patrol.team.organization)
        | Q(district=request.user.patrol.team.district)
    )

    return render(request, "wiki/index.html", {"folders": folders, "pages": pages})


@login_required
def page(request, page_id):
    page = get_object_or_404(Page, id=page_id)
    return render(request, "wiki/page.html", {"page": page})
