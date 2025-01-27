"""
Django view decorators can be used to restrict the execution of a view function on certain conditions.

For more information, see :doc:`topics/http/decorators`.
"""
import time
from functools import wraps

from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from .models import Region


def staff_required(function):
    """
    This decorator can be used to make sure a view can only be retrieved by users who are either staff or superusers.

    :param function: The view function which should be protected
    :type function: ~collections.abc.Callable

    :return: The decorated function
    :rtype: ~collections.abc.Callable
    """

    def is_staff(user):
        """
        This function checks, whether or not a user is a superuser or staff member.

        :param user: The user, that is checked
        :type user: ~integreat_cms.cms.models.users.user.User

        :raises ~django.core.exceptions.PermissionDenied: If user doesn't have the permission to access the staff area

        :return: whether or not the user is staff member
        :rtype: bool
        """

        if user.is_superuser or user.is_staff:
            return True
        raise PermissionDenied(
            f"{user!r} does not have the permission to access this staff area"
        )

    return user_passes_test(is_staff)(function)


def permission_required(permission):
    """
    Decorator for views that checks whether a user has a particular permission enabled.
    If not, the PermissionDenied exception is raised.

    :param permission: The required permission
    :type permission: str

    :return: The decorated function
    :rtype: ~collections.abc.Callable
    """

    def check_permission(user):
        """
        This function checks the permission of a user

        :param user: The user, that is checked
        :type user: ~integreat_cms.cms.models.users.user.User

        :raises ~django.core.exceptions.PermissionDenied: If user doesn't have the given permission

        :return: Whether the user has the permission or not
        :rtype: bool
        """

        if user.has_perm(permission):
            return True
        raise PermissionDenied(f"{user!r} does not have the permission {permission!r}")

    return user_passes_test(check_permission)


def region_permission_required(function):
    """
    This decorator can be used to make sure a view can only be retrieved by users of the requested region.

    :param function: The view function which should be protected
    :type function: ~collections.abc.Callable

    :return: The decorated function
    :rtype: ~collections.abc.Callable
    """

    @wraps(function)
    def wrap(request, *args, **kwargs):
        """
        The inner function for this decorator

        ::param request: Django request
        :type request: ~django.http.HttpRequest

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied kwargs
        :type kwargs: dict

        :raises ~django.core.exceptions.PermissionDenied: If user doesn't have the permission to access the region

        :return: the decorated function
        :rtype: ~collections.abc.Callable
        """
        user = request.user
        # superusers and staff have permissions for all regions
        if user.is_superuser or user.is_staff:
            return function(request, *args, **kwargs)
        region = Region.get_current_region(request)
        if region in user.regions.all():
            return function(request, *args, **kwargs)
        raise PermissionDenied(
            f"{user!r} does not have the permission to access {region!r}"
        )

    return wrap


def modify_mfa_authenticated(function):
    """
    This decorator can be used to make sure a user can only modify his 2FA settings when he has a valid 2FA session.

    :param function: The view function which should be protected
    :type function: ~collections.abc.Callable

    :return: The decorated function
    :rtype: ~collections.abc.Callable
    """

    @wraps(function)
    def wrap(request, *args, **kwargs):
        """
        The inner function for this decorator

        :param request: Django request
        :type request: ~django.http.HttpRequest

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied kwargs
        :type kwargs: dict

        :return: the decorated function
        :rtype: ~collections.abc.Callable
        """
        if not "modify_mfa_authentication_time" in request.session or request.session[
            "modify_mfa_authentication_time"
        ] < (time.time() - 5 * 60):
            request.session["mfa_redirect_url"] = request.path
            return redirect("authenticate_modify_mfa")
        return function(request, *args, **kwargs)

    return wrap
