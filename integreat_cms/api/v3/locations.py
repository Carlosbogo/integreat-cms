from django.conf import settings
from django.http import JsonResponse

from ...cms.models import Region
from ..decorators import json_response


def transform_poi(poi, poi_translation):
    """
    Function to create a JSON from a single poi object.
    Because the json requires a translated name, `poi_translation` has to be
    passed as the second parameter.

    :param poi: The poi object which should be converted
    :type poi: ~integreat_cms.cms.models.pois.poi.POI

    :param poi_translation: The translation of the POI which should be used for the title
    :type poi_translation: ~integreat_cms.cms.models.pois.poi_translation.POITranslation

    :return: data necessary for API
    :rtype: dict
    """
    return {
        "id": poi.id,
        "name": poi_translation.title,
        "address": poi.address,
        "town": poi.city,
        "state": None,
        "postcode": poi.postcode,
        "region": None,
        "country": poi.country,
        "latitude": poi.latitude,
        "longitude": poi.longitude,
    }


def transform_poi_translation(poi_translation):
    """
    Function to create a JSON from a single poi_translation object.

    :param poi_translation: The poi translation object which should be converted
    :type poi_translation: ~integreat_cms.cms.models.pois.poi_translation.POITranslation

    :return: data necessary for API
    :rtype: dict
    """

    poi = poi_translation.poi
    return {
        "id": poi_translation.id,
        "url": settings.WEBAPP_URL + poi_translation.get_absolute_url(),
        "path": poi_translation.get_absolute_url(),
        "title": poi_translation.title,
        "modified_gmt": poi_translation.last_updated.strftime("%Y-%m-%d %H:%M:%S"),
        "excerpt": poi_translation.short_description,
        "content": poi_translation.description,
        "available_languages": poi_translation.available_languages,
        "thumbnail": poi.icon.url if poi.icon else None,
        "location": transform_poi(poi, poi_translation),
        "hash": None,
    }


@json_response
# pylint: disable=unused-argument
def locations(request, region_slug, language_slug):
    """
    List all POIs of the region and transform result into JSON

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the requested region
    :type region_slug: str

    :param language_slug: The slug of the requested language
    :type language_slug: str

    :return: JSON object according to APIv3 locations endpoint definition
    :rtype: ~django.http.JsonResponse
    """
    region = Region.get_current_region(request)
    result = []
    for poi in region.pois.filter(archived=False):
        translation = poi.get_public_translation(language_slug)
        if translation:
            result.append(transform_poi_translation(translation))

    return JsonResponse(
        result, safe=False
    )  # Turn off Safe-Mode to allow serializing arrays
