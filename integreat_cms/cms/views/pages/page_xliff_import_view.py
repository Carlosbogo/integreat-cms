import os
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ....xliff.utils import get_xliff_import_diff, xliff_import_confirm
from ...decorators import region_permission_required, permission_required
from ...models import Region
from .page_context_mixin import PageContextMixin

logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
@method_decorator(permission_required("cms.view_page"), name="dispatch")
class PageXliffImportView(TemplateView, PageContextMixin):
    """
    View for importing uploaded XLIFF files
    """

    #: Template for XLIFF import view
    template_name = "pages/page_xliff_import_view.html"

    # Custom attributes:
    #: The region of this view
    region = None
    #: The language of this view
    language = None
    #: The upload directory of this import
    xliff_dir = None

    def get_context_data(self, **kwargs):
        """
        Returns a dictionary representing the template context
        (see :meth:`~django.views.generic.base.ContextMixin.get_context_data`).

        :param kwargs: The given keyword arguments
        :Type kwargs: dict

        :return: The template context
        :rtype: dict
        """
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "current_menu_item": "pages",
                "upload_dir": os.path.basename(self.xliff_dir),
                "translation_diffs": get_xliff_import_diff(
                    self.request, self.xliff_dir
                ),
                "language": self.language,
            }
        )
        return context

    def dispatch(self, request, *args, **kwargs):
        """
        Redirect to page tree if XLIFF directory does not exist

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        # Get current region and language
        self.region = Region.get_current_region(request)
        self.language = get_object_or_404(
            self.region.languages, slug=kwargs.get("language_slug")
        )
        # Get directory path of the uploaded XLIFF files
        self.xliff_dir = os.path.join(
            settings.XLIFF_UPLOAD_DIR, kwargs.get("xliff_dir")
        )

        if not os.path.isdir(self.xliff_dir):
            messages.error(
                request,
                _("This XLIFF import is no longer available."),
            )
            return redirect(
                "pages",
                **{
                    "region_slug": self.region.slug,
                    "language_slug": self.language.slug,
                },
            )
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Confirm the xliff import

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        logger.info(
            "XLIFF files of directory %r imported by %r",
            self.xliff_dir,
            request.user,
        )
        if xliff_import_confirm(request, self.xliff_dir):
            return redirect(
                "pages",
                **{
                    "region_slug": self.region.slug,
                    "language_slug": self.language.slug,
                },
            )
        return self.render_to_response(self.get_context_data(**kwargs))