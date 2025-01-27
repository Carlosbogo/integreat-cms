"""
This module contains view actions related to pages.
"""
import json
import logging
import os
import uuid

from mptt.exceptions import InvalidMove

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseNotFound, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST

from ....xliff.utils import pages_to_xliff_file
from ...constants import text_directions
from ...decorators import region_permission_required, permission_required
from ...forms import PageForm
from ...models import Page, Region, PageTranslation
from ...utils.file_utils import extract_zip_archive
from ...utils.pdf_utils import generate_pdf
from ...utils.translation_utils import ugettext_many_lazy as __

logger = logging.getLogger(__name__)


@require_POST
@login_required
@region_permission_required
def archive_page(request, page_id, region_slug, language_slug):
    """
    Archive page object

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param page_id: The id of the page which should be archived
    :type page_id: int

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to edit the specific page

    :return: A redirection to the :class:`~integreat_cms.cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
    """

    region = Region.get_current_region(request)
    page = get_object_or_404(region.pages, id=page_id)

    if not request.user.has_perm("cms.change_page_object", page):
        raise PermissionDenied(
            f"{request.user!r} does not have the permission to archive {page!r}"
        )

    page.explicitly_archived = True
    page.save()

    logger.debug("%r archived by %r", page, request.user)
    messages.success(request, _("Page was successfully archived"))

    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@require_POST
@login_required
@region_permission_required
def restore_page(request, page_id, region_slug, language_slug):
    """
    Restore page object (set ``archived=False``)

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param page_id: The id of the page which should be restored
    :type page_id: int

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to edit the specific page

    :return: A redirection to the :class:`~integreat_cms.cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
    """

    region = Region.get_current_region(request)
    page = get_object_or_404(region.pages, id=page_id)

    if not request.user.has_perm("cms.change_page_object", page):
        raise PermissionDenied(
            f"{request.user!r} does not have the permission to restore {page!r}"
        )

    page.explicitly_archived = False
    page.save()

    if page.implicitly_archived:
        logger.debug(
            "%r restored by %r but still implicitly archived",
            page,
            request.user,
        )
        messages.info(
            request,
            _("Page was successfully restored.")
            + " "
            + _(
                "However, it is still archived because one of its parent pages is archived."
            ),
        )
        return redirect(
            "archived_pages",
            **{
                "region_slug": region_slug,
                "language_slug": language_slug,
            },
        )
    logger.debug("%r restored by %r", page, request.user)
    messages.success(request, _("Page was successfully restored."))
    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@login_required
@region_permission_required
@permission_required("cms.view_page")
# pylint: disable=unused-argument
def view_page(request, page_id, region_slug, language_slug):
    """
    View page object

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param page_id: The id of the page which should be viewed
    :type page_id: int

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :return: A redirection to the :class:`~integreat_cms.cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
    """

    region = Region.get_current_region(request)
    page = get_object_or_404(region.pages, id=page_id)

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "pages/page_view.html"

    page_translation = page.get_translation(language_slug)
    mirrored_translation = page.get_mirrored_page_translation(language_slug)

    return render(
        request,
        template_name,
        {
            "page_translation": page_translation,
            "mirrored_translation": mirrored_translation,
            "mirrored_page_first": page.mirrored_page_first,
            "right_to_left": page_translation.language.text_direction
            == text_directions.RIGHT_TO_LEFT,
        },
    )


@require_POST
@login_required
@region_permission_required
@permission_required("cms.delete_page")
def delete_page(request, page_id, region_slug, language_slug):
    """
    Delete page object

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param page_id: The id of the page which should be deleted
    :type page_id: int

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :return: A redirection to the :class:`~integreat_cms.cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
    """

    region = Region.get_current_region(request)
    page = get_object_or_404(region.pages, id=page_id)

    if page.children.exists():
        messages.error(request, _("You cannot delete a page which has subpages."))
    else:
        logger.info("%r deleted by %r", page, request.user)
        page.delete()
        messages.success(request, _("Page was successfully deleted"))

    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@login_required
@region_permission_required
@permission_required("cms.view_page")
# pylint: disable=unused-argument
def export_pdf(request, region_slug, language_slug):
    """
    Function for handling a pdf export request for pages.
    The pages get extracted from request.GET attribute and the request is forwarded to :func:`~integreat_cms.cms.utils.pdf_utils.generate_pdf`

    :param request: Request submitted for rendering pdf document
    :type request: ~django.http.HttpRequest

    :param region_slug: unique region slug
    :type region_slug: str

    :param language_slug: bcp47 slug of the current language
    :type language_slug: str

    :return: PDF document offered for download
    :rtype: ~django.http.HttpResponse
    """
    region = Region.get_current_region(request)
    # retrieve the selected page ids
    page_ids = request.POST.getlist("selected_ids[]")
    # collect the corresponding page objects
    pages = region.pages.filter(explicitly_archived=False, id__in=page_ids)
    # generate PDF document wrapped in a HtmlResponse object
    response = generate_pdf(region, language_slug, pages)
    if response.status_code == 200:
        # offer PDF document for download
        response["Content-Disposition"] = (
            response["Content-Disposition"] + "; attachment"
        )
    return response


def expand_page_translation_id(request, short_url_id):
    """
    Searches for a page translation with corresponding ID and redirects browser to web app

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param short_url_id: The id of the requested page
    :type short_url_id: int

    :return: A redirection to :class:`~integreat_cms.core.settings.WEBAPP_URL`
    :rtype: ~django.http.HttpResponseRedirect
    """

    page_translation = PageTranslation.objects.get(
        id=short_url_id
    ).latest_public_revision

    if page_translation and not page_translation.page.archived:
        return redirect(settings.WEBAPP_URL + page_translation.get_absolute_url())
    return HttpResponseNotFound("<h1>Page not found</h1>")


@login_required
@region_permission_required
@permission_required("cms.view_page")
def download_xliff(request, region_slug, language_slug):
    """
    Download a zip file of XLIFF files.
    The target languages and pages are selected and the source languages automatically determined.

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the target language
    :type language_slug: str

    :return: A redirection to the :class:`~integreat_cms.cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
    """

    page_ids = request.POST.getlist("selected_ids[]")

    if not page_ids:
        messages.error(
            request,
            _("No pages selected for XLIFF export."),
        )
        return redirect(
            "pages",
            **{
                "region_slug": region_slug,
                "language_slug": language_slug,
            },
        )

    region = Region.get_current_region(request)
    pages = get_list_or_404(region.pages, id__in=page_ids)

    target_language = get_object_or_404(
        region.language_tree_nodes,
        language__slug=language_slug,
        parent__isnull=False,
    ).language

    xliff_file_url = pages_to_xliff_file(request, pages, target_language)
    if xliff_file_url:
        # Insert link with automatic download into success message
        messages.success(
            request,
            __(
                _("XLIFF file for translation to {} successfully created.").format(
                    target_language
                ),
                _(
                    "If the download does not start automatically, please click {}here{}."
                ).format(
                    f"<a data-auto-download href='{xliff_file_url}' class='font-bold underline hover:no-underline' download>",
                    "</a>",
                ),
            ),
        )

    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@require_POST
@login_required
@region_permission_required
@permission_required("cms.change_page")
# pylint: disable=unused-argument
def post_translation_state_ajax(request, region_slug):
    """
    This view is called for manually unseting the translation process

    :param request: ajax request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :return: on success returns language of updated translation
    :rtype: ~django.http.JsonResponse
    """
    decoded_json = json.loads(request.body.decode("utf-8"))
    target_language = decoded_json["language"]
    page_id = decoded_json["pageId"]
    translation_state = decoded_json["translationState"]
    region = Region.get_current_region(request)
    page = get_object_or_404(region.pages, id=page_id)
    page_translation = page.get_translation(target_language.code)
    if page_translation:
        page_translation.update(currently_in_translation=translation_state)
        return JsonResponse({"language": target_language})
    return JsonResponse(
        {"error": _("Could not update page translation state")}, status=400
    )


@require_POST
@login_required
@region_permission_required
@permission_required("cms.change_page")
def upload_xliff(request, region_slug, language_slug):
    """
    Upload and import an XLIFF file

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :return: A redirection to the :class:`~integreat_cms.cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
    """
    xliff_paths = []
    upload_files = request.FILES.getlist("xliff_file")
    xliff_dir_uuid = str(uuid.uuid4())
    if upload_files:
        logger.debug("Uploaded files: %r", upload_files)
        upload_dir = os.path.join(settings.XLIFF_UPLOAD_DIR, xliff_dir_uuid)
        os.makedirs(upload_dir, exist_ok=True)
        for upload_file in upload_files:
            # Check whether the file is valid
            if not upload_file.name.endswith((".zip", ".xliff", ".xlf")):
                # File type not supported
                messages.error(
                    request,
                    _('File "{}" is neither a ZIP archive nor an XLIFF file.').format(
                        upload_file.name
                    ),
                )
                logger.warning(
                    "%r tried to import the file %r which is neither a ZIP archive nor an XLIFF file",
                    request.user,
                    upload_file.name,
                )
                continue

            # Copy uploaded file from its temporary location into the upload directory
            with open(os.path.join(upload_dir, upload_file.name), "wb+") as file_write:
                # Using chunks() instead of read() ensures that large files don’t overwhelm your system’s memory
                for chunk in upload_file.chunks():
                    file_write.write(chunk)

            if upload_file.name.endswith(".zip"):
                # Extract zip archive
                xliff_paths_tmp, invalid_file_paths = extract_zip_archive(
                    os.path.join(upload_dir, upload_file.name), upload_dir
                )
                # Append contents of zip archive to total list of xliff files
                xliff_paths += xliff_paths_tmp
                if not xliff_paths_tmp:
                    messages.error(
                        request,
                        _('The ZIP archive "{}" does not contain XLIFF files.').format(
                            upload_file.name
                        ),
                    )
                elif invalid_file_paths:
                    messages.warning(
                        request,
                        _(
                            'The ZIP archive "{}" contains the following invalid files: "{}"'
                        ).format(upload_file.name, '", "'.join(invalid_file_paths)),
                    )
            else:
                # If file is an xliff file, directly append it to the paths
                xliff_paths.append(os.path.join(upload_dir, upload_file.name))
        # Check if at least one file was uploaded successfully
        if xliff_paths:
            logger.info(
                "XLIFF files %r uploaded into %r by %r",
                xliff_paths,
                upload_dir,
                request.user,
            )
            return redirect(
                "import_xliff",
                **{
                    "region_slug": region_slug,
                    "language_slug": language_slug,
                    "xliff_dir": xliff_dir_uuid,
                },
            )
    else:
        messages.error(
            request,
            _("No XLIFF file was selected for import."),
        )

    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@require_POST
@login_required
@region_permission_required
@permission_required("cms.change_page")
# pylint: disable=too-many-arguments
def move_page(request, region_slug, language_slug, page_id, target_id, position):
    """
    Move a page object in the page tree

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :param page_id: The id of the page which should be moved
    :type page_id: int

    :param target_id: The id of the page which determines the new position
    :type target_id: int

    :param position: The new position of the page relative to the target (choices: :mod:`~integreat_cms.cms.constants.position`)
    :type position: str

    :return: A redirection to the :class:`~integreat_cms.cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
    """

    region = Region.get_current_region(request)
    page = get_object_or_404(region.pages, id=page_id)
    target = get_object_or_404(region.pages, id=target_id)

    try:
        page.move_to(target, position)
        logger.debug(
            "%r moved to %r of %r by %r",
            page,
            position,
            target,
            request.user,
        )
        messages.success(
            request,
            _('The page "{page}" was successfully moved.').format(
                page=page.best_translation.title
            ),
        )
    except (ValueError, InvalidMove) as e:
        messages.error(request, e)
        logger.exception(e)

    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@require_POST
@login_required
@region_permission_required
@permission_required("cms.change_page")
@permission_required("cms.grant_page_permissions")
# pylint: disable=too-many-branches
def grant_page_permission_ajax(request):
    """
    Grant a user editing or publishing permissions on a specific page object

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :raises ~django.core.exceptions.PermissionDenied: If page permissions are disabled for this region or the user does
                                                      not have the permission to grant page permissions

    :return: The rendered page permission table
    :rtype: ~django.template.response.TemplateResponse
    """

    try:
        data = json.loads(request.body.decode("utf-8"))
        permission = data.get("permission")
        page = Page.objects.get(id=data.get("page_id"))
        user = get_user_model().objects.get(id=data.get("user_id"))

        logger.debug(
            "[AJAX] %r wants to grant %r the permission to %s %r",
            request.user,
            user,
            permission,
            page,
        )

        if not page.region.page_permissions_enabled:
            raise PermissionDenied(
                f"Page permissions are not activated for {page.region!r}"
            )

        if not (request.user.is_superuser or request.user.is_staff):
            # additional checks if requesting user is no superuser or staff
            if page.region not in request.user.regions:
                # requesting user can only grant permissions for pages of his region
                logger.warning(
                    "Error: %r cannot grant permissions for %r",
                    request.user,
                    page.region,
                )
                raise PermissionDenied
            if page.region not in user.regions:
                # user can only receive permissions for pages of his region
                logger.warning(
                    "Error: %r cannot receive permissions for %r",
                    user,
                    page.region,
                )
                raise PermissionDenied

        if permission == "edit":
            # check, if the user already has this permission
            if user.has_perm("cms.change_page_object", page):
                message = _(
                    "Information: The user {user} has this permission already."
                ).format(user=user.username)
                level_tag = "info"
            else:
                # else grant the permission by adding the user to the editors of the page
                page.editors.add(user)
                page.save()
                message = _("Success: The user {user} can now edit this page.").format(
                    user=user.username
                )
                level_tag = "success"
        elif permission == "publish":
            # check, if the user already has this permission
            if user.has_perm("cms.publish_page_object", page):
                message = _(
                    "Information: The user {user} has this permission already."
                ).format(user=user.username)
                level_tag = "info"
            else:
                # else grant the permission by adding the user to the publishers of the page
                page.publishers.add(user)
                page.save()
                message = _(
                    "Success: The user {user} can now publish this page."
                ).format(user=user.username)
                level_tag = "success"
        else:
            logger.warning("Error: The permission %r is not supported", permission)
            raise PermissionDenied
    # pylint: disable=broad-except
    except Exception as e:
        logger.exception(e)
        message = _("An error has occurred. Please contact an administrator.")
        level_tag = "error"

    logger.debug(message)

    return render(
        request,
        "pages/_page_permission_table.html",
        {
            "page": page,
            "page_form": PageForm(
                instance=page,
                additional_instance_attributes={
                    "region": page.region,
                },
            ),
            "permission_message": {"message": message, "level_tag": level_tag},
        },
    )


@require_POST
@login_required
@region_permission_required
@permission_required("cms.change_page")
@permission_required("cms.grant_page_permissions")
# pylint: disable=too-many-branches
def revoke_page_permission_ajax(request):
    """
    Remove a page permission for a given user and page

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :raises ~django.core.exceptions.PermissionDenied: If page permissions are disabled for this region or the user does
                                                      not have the permission to revoke page permissions

    :return: The rendered page permission table
    :rtype: ~django.template.response.TemplateResponse
    """

    try:
        data = json.loads(request.body.decode("utf-8"))
        permission = data.get("permission")
        page = Page.objects.get(id=data.get("page_id"))
        user = get_user_model().objects.get(id=data.get("user_id"))

        logger.debug(
            "[AJAX] %r wants to revoke the permission to %s %r from %r",
            request.user,
            permission,
            page,
            user,
        )

        if not page.region.page_permissions_enabled:
            raise PermissionDenied(
                f"Page permissions are not activated for {page.region!r}"
            )

        if not (request.user.is_superuser or request.user.is_staff):
            # additional checks if requesting user is no superuser or staff
            if page.region not in request.user.regions:
                # requesting user can only revoke permissions for pages of his region
                logger.warning(
                    "Error: %r cannot revoke permissions for %r",
                    request.user,
                    page.region,
                )
                raise PermissionDenied

        if permission == "edit":
            if user in page.editors.all():
                # revoke the permission by removing the user to the editors of the page
                page.editors.remove(user)
                page.save()
            # check, if the user has this permission anyway
            if user.has_perm("cms.change_page_object", page):
                message = _(
                    "Information: The user {user} has been removed from the editors of this page, "
                    "but has the implicit permission to edit this page anyway."
                ).format(user=user.username)
                level_tag = "info"
            else:
                message = _(
                    "Success: The user {user} cannot edit this page anymore."
                ).format(user=user.username)
                level_tag = "success"
        elif permission == "publish":
            if user in page.publishers.all():
                # revoke the permission by removing the user to the publishers of the page
                page.publishers.remove(user)
                page.save()
            # check, if the user already has this permission
            if user.has_perm("cms.publish_page_object", page):
                message = _(
                    "Information: The user {user} has been removed from the publishers of this page, "
                    "but has the implicit permission to publish this page anyway."
                ).format(user=user.username)
                level_tag = "info"
            else:
                message = _(
                    "Success: The user {user} cannot publish this page anymore."
                ).format(user=user.username)
                level_tag = "success"
        else:
            logger.warning("Error: The permission %r is not supported", permission)
            raise PermissionDenied
    # pylint: disable=broad-except
    except Exception as e:
        logger.exception(e)
        message = _("An error has occurred. Please contact an administrator.")
        level_tag = "error"

    logger.debug(message)

    return render(
        request,
        "pages/_page_permission_table.html",
        {
            "page": page,
            "page_form": PageForm(
                instance=page,
                additional_instance_attributes={
                    "region": page.region,
                },
            ),
            "permission_message": {"message": message, "level_tag": level_tag},
        },
    )


@login_required
@region_permission_required
@permission_required("cms.view_page")
# pylint: disable=unused-argument
def get_page_order_table_ajax(request, region_slug, page_id, parent_id):
    """
    Retrieve the order table for a given page and a given parent page.
    This is used in the page form to change the order of a page relative to its siblings.

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param page_id: The id of the page of the current page form
    :type page_id: int

    :param parent_id: The id of the parent page to which the order table should be returned
    :type parent_id: int

    :return: The rendered page order table
    :rtype: ~django.template.response.TemplateResponse
    """

    region = Region.get_current_region(request)
    page = get_object_or_404(region.pages, id=page_id)

    if parent_id == "0":
        siblings = region.pages.filter(level=0)
    else:
        siblings = region.pages.filter(parent__id=parent_id)

    logger.debug(
        "Page order table for %r and siblings %r",
        page,
        siblings,
    )

    return render(
        request,
        "pages/_page_order_table.html",
        {
            "page": page,
            "siblings": siblings,
        },
    )


@login_required
@region_permission_required
@permission_required("cms.view_page")
# pylint: disable=unused-argument
def get_new_page_order_table_ajax(request, region_slug, parent_id):
    """
    Retrieve the order table for a new page and a given parent page.
    This is used in the page form to set the position of a new page relative to its siblings.

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param parent_id: The id of the parent page to which the order table should be returned
    :type parent_id: int

    :return: The rendered page order table
    :rtype: ~django.template.response.TemplateResponse
    """

    region = Region.get_current_region(request)

    if parent_id == "0":
        siblings = region.pages.filter(level=0)
    else:
        siblings = region.pages.filter(parent__id=parent_id)

    logger.debug(
        "Page order table for a new page and siblings %r",
        siblings,
    )

    return render(
        request,
        "pages/_page_order_table.html",
        {
            "siblings": siblings,
        },
    )


@login_required
@region_permission_required
@permission_required("cms.view_page")
# pylint: disable=unused-argument
def render_mirrored_page_field(request, region_slug):
    """
    Retrieve the rendered mirrored page field template

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param region_slug: The slug of the current region
    :type region_slug: str

    :return: The rendered mirrored page field
    :rtype: ~django.template.response.TemplateResponse
    """
    # Get the region from which the content should be embedded
    region = get_object_or_404(Region, id=request.GET.get("region_id"))
    # Get the page in which the content should be embedded (to exclude it from the possible selections)
    page = Page.objects.filter(id=request.GET.get("page_id")).first()
    page_form = PageForm(
        data={"mirrored_page_region": region.id},
        instance=page,
        additional_instance_attributes={
            "region": region,
        },
    )
    return render(
        request,
        "pages/_mirrored_page_field.html",
        {
            "page_form": page_form,
        },
    )
