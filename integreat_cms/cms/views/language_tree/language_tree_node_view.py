import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...decorators import region_permission_required, permission_required
from ...forms import LanguageTreeNodeForm
from ...models import Region

logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
@method_decorator(permission_required("cms.view_languagetreenode"), name="dispatch")
@method_decorator(permission_required("cms.change_languagetreenode"), name="post")
class LanguageTreeNodeView(TemplateView):
    """
    Class that handles viewing single language in the language tree.
    This view is available within regions.
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "language_tree/language_tree_node_form.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {"current_menu_item": "language_tree_form"}

    def get(self, request, *args, **kwargs):
        """
        Render :class:`~integreat_cms.cms.forms.language_tree.language_tree_node_form.LanguageTreeNodeForm`

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        # current region
        region = Region.get_current_region(request)
        # current language tree node
        language_tree_node = region.language_tree_nodes.filter(
            id=kwargs.get("language_tree_node_id")
        ).first()

        language_tree_node_form = LanguageTreeNodeForm(
            instance=language_tree_node,
            additional_instance_attributes={
                "region": region,
            },
        )
        return render(
            request,
            self.template_name,
            {
                "language_tree_node_form": language_tree_node_form,
                **self.base_context,
            },
        )

    # pylint: disable=unused-argument
    def post(self, request, *args, **kwargs):
        """
        Save and show form for editing a single language (HTTP POST) in the language tree

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        # current region
        region = Region.get_current_region(request)
        # current language tree node
        language_tree_node_instance = region.language_tree_nodes.filter(
            id=kwargs.get("language_tree_node_id")
        ).first()
        language_tree_node_form = LanguageTreeNodeForm(
            data=request.POST,
            instance=language_tree_node_instance,
            additional_instance_attributes={
                "region": region,
            },
        )

        if not language_tree_node_form.is_valid():
            # Add error messages
            language_tree_node_form.add_error_messages(request)
        elif not language_tree_node_form.has_changed():
            # Add "no changes" messages
            messages.info(request, _("No changes made"))
        else:
            # Save form
            language_tree_node_form.save()
            # Add the success message and redirect to the edit page
            if not language_tree_node_instance:
                messages.success(
                    request,
                    _('Language tree node for "{}" was successfully saved').format(
                        language_tree_node_form.instance
                    ),
                )
                return redirect(
                    "edit_language_tree_node",
                    **{
                        "language_tree_node_id": language_tree_node_form.instance.id,
                        "region_slug": region.slug,
                    }
                )
            # Add the success message
            messages.success(
                request,
                _('Language tree node for "{}" was successfully created').format(
                    language_tree_node_form.instance
                ),
            )
        return render(
            request,
            self.template_name,
            {"language_tree_node_form": language_tree_node_form, **self.base_context},
        )
