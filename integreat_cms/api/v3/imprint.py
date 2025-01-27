"""
imprint API endpoint
"""
from django.conf import settings
from django.http import JsonResponse

from ...cms.models import Region
from ..decorators import json_response


def transform_imprint(imprint_translation):
    """
    Function to create a JSON from a single imprint_translation object.

    :param imprint_translation: single page translation object
    :type imprint_translation: ~integreat_cms.cms.models.pages.page_translation.PageTranslation

    :return: data necessary for API
    :rtype: dict
    """
    if imprint_translation.page.icon:
        thumbnail = settings.BASE_URL + imprint_translation.page.icon.url
    else:
        thumbnail = None
    return {
        "id": imprint_translation.id,
        "url": imprint_translation.permalink,
        "title": imprint_translation.title,
        "modified_gmt": imprint_translation.last_updated,
        "excerpt": imprint_translation.text,
        "content": imprint_translation.text,
        "parent": None,
        "available_languages": imprint_translation.available_languages,
        "thumbnail": thumbnail,
        "hash": None,
    }


@json_response
# pylint: disable=unused-argument
def imprint(request, region_slug, language_slug):
    """
    Get imprint for language and return JSON object to client. If no imprint translation
    is available in the selected language, try to return the translation in the region
    default language.

    :param request: Django request
    :type request: ~django.http.HttpRequest
    :param region_slug: slug of a region
    :type region_slug: str
    :param language_slug: language slug
    :type language_slug: str

    :return: JSON object according to APIv3 imprint endpoint definition
    :rtype: ~django.http.JsonResponse
    """
    region = Region.get_current_region(request)
    if hasattr(region, "imprint"):
        imprint_translation = region.imprint.get_public_translation(language_slug)
        if imprint_translation:
            return JsonResponse(transform_imprint(imprint_translation))
        if region.default_language:
            imprint_default_translation = region.imprint.get_public_translation(
                region.default_language.slug
            )
            if imprint_default_translation:
                return JsonResponse(transform_imprint(imprint_default_translation))
    # If imprint does not exist, return an empty response. Turn off Safe-Mode to allow serializing arrays
    return JsonResponse([], safe=False)
