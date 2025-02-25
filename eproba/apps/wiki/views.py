from apps.users.utils import min_function, patrol_required
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import PageForm
from .models import Folder, Page


@login_required
def folder(request, folder_id=None):
    """
    Render the index view for a given folder or the root level.
    """
    if folder_id:
        folder_instance = get_object_or_404(Folder, id=folder_id)
        children_folders = [
            child
            for child in folder_instance.get_children()
            if child.can_view(request.user)
        ]
        folder_pages = [
            page for page in folder_instance.get_pages() if page.can_view(request.user)
        ]
        context = {
            "folders": children_folders,
            "pages": folder_pages,
            "current_folder": folder_instance,
            "allow_edit": folder_instance.can_edit(request.user),
        }
        return render(request, "wiki/index.html", context)

    # For root-level view, build an access filter once.
    access_filter = (
        Q(owner=request.user)
        | Q(for_all=True)
        | Q(team=request.user.patrol.team)
        | Q(patrol=request.user.patrol)
        | Q(organization=request.user.patrol.team.organization)
        | Q(district=request.user.patrol.team.district)
    )
    root_folders = Folder.get_root_nodes().filter(access_filter)
    root_pages = Page.objects.filter(folder=None).filter(access_filter)
    context = {
        "folders": root_folders,
        "pages": root_pages,
        "allow_wiki_init": request.user.function >= 3
        and not root_folders.filter(team=request.user.patrol.team).exists(),
        "allow_edit": request.user.is_staff
        and request.user.has_perm("wiki.add_folder"),
    }
    return render(request, "wiki/index.html", context)


@login_required
def page(request, page_id):
    """Display a single page."""
    page_instance = get_object_or_404(Page, id=page_id)
    return render(
        request,
        "wiki/page.html",
        {"page": page_instance, "allow_edit": page_instance.can_edit(request.user)},
    )


@patrol_required
@min_function(3)
def init_wiki(request):
    """Initialize the wiki by creating a root folder for the patrol team if none exists."""
    if Folder.objects.filter(team=request.user.patrol.team).exists():
        return redirect("wiki:index")
    new_folder = Folder.add_root(
        name=request.user.patrol.team.name,
        owner=request.user,
        team=request.user.patrol.team,
    )
    return redirect("wiki:folder", folder_id=new_folder.id)


@login_required
@require_http_methods(["POST"])
def create_folder(request, folder_id=None):
    """
    Create a new folder.
      - If a parent folder is specified, create a child folder.
      - Otherwise, create a root-level folder (if permitted).
    """
    name = request.POST.get("name")
    if folder_id:
        parent = get_object_or_404(Folder, id=folder_id)
        if not parent.can_edit(request.user):
            return redirect("wiki:folder", folder_id=folder_id)
        if name:
            new_folder = parent.add_child(name=name, owner=request.user)
            return redirect("wiki:folder", folder_id=new_folder.id)
        return redirect("wiki:folder", folder_id=folder_id)
    elif request.user.is_staff and request.user.has_perm("wiki.add_folder"):
        if name:
            new_folder = Folder.add_root(name=name, owner=request.user)
            return redirect("wiki:folder", folder_id=new_folder.id)
    return redirect("wiki:index")


@login_required
def create_page(request, folder_id=None):
    """
    Create a new page.
        - If a folder is specified, create a page in that folder.
        - Otherwise, create a root-level page.
    """
    folder_instance = None
    if folder_id:
        folder_instance = get_object_or_404(Folder, id=folder_id)
        if not folder_instance.can_edit(request.user):
            return redirect("wiki:folder", folder_id=folder_id)

    if request.method == "POST":
        form = PageForm(request.POST)
        if form.is_valid():
            new_page = form.save(commit=False)
            new_page.owner = request.user
            if folder_instance:
                new_page.folder = folder_instance
            new_page.save()
            return redirect("wiki:page", page_id=new_page.id)
    else:
        form = PageForm()

    context = {"form": form}
    if folder_instance:
        context["folder"] = folder_instance
    return render(request, "wiki/create_page.html", context)


def edit_folder(request, folder_id):
    """Edit the folder name."""
    folder_instance = get_object_or_404(Folder, id=folder_id)
    if not folder_instance.can_edit(request.user):
        return redirect("wiki:folder", folder_id=folder_id)

    if request.method == "POST":
        name = request.POST.get("name")
        if name:
            folder_instance.name = name
            folder_instance.save()
    return redirect("wiki:folder", folder_id=folder_id)


def edit_page(request, page_id):
    """Edit the page content."""
    page_instance = get_object_or_404(Page, id=page_id)
    if not page_instance.can_edit(request.user):
        return redirect("wiki:page", page_id=page_id)

    if request.method == "POST":
        form = PageForm(request.POST, instance=page_instance)
        if form.is_valid():
            form.save()
            return redirect("wiki:page", page_id=page_id)
    else:
        form = PageForm(instance=page_instance)

    return render(request, "wiki/edit_page.html", {"form": form, "page": page_instance})
