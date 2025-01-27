from datetime import timedelta
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone

from ...cms.models import Region
from ...cms.models.events.event_translation import EventTranslation
from ...cms.utils.slug_utils import generate_unique_slug
from ..decorators import json_response
from .locations import transform_poi


def transform_event(event):
    """
    Function to create a JSON from a single event object.

    :param event: The event which should be converted
    :type event: ~integreat_cms.cms.models.events.event.Event

    :return: data necessary for API
    :rtype: dict
    """
    return {
        "id": event.id,
        "start_date": event.start_date,
        "end_date": event.end_date,
        "all_day": event.is_all_day,
        "start_time": event.start_time,
        "end_time": event.end_time,
        "recurrence_id": event.recurrence_rule.id if event.recurrence_rule else None,
        "timezone": settings.CURRENT_TIME_ZONE,
    }


def transform_event_translation(event_translation):
    """
    Function to create a JSON from a single event_translation object.

    :param event_translation: The event translation object which should be converted
    :type event_translation: ~integreat_cms.cms.models.events.event_translation.EventTranslation

    :return: data necessary for API
    :rtype: dict
    """

    event = event_translation.event
    if event.location:
        location_translation = (
            event.location.get_public_translation(event_translation.language.slug)
            or event.location.default_translation
        )
        location = transform_poi(event.location, location_translation)
    else:
        location = None

    return {
        "id": event_translation.id,
        "url": settings.WEBAPP_URL + event_translation.get_absolute_url(),
        "path": event_translation.get_absolute_url(),
        "title": event_translation.title,
        "modified_gmt": event_translation.last_updated.strftime("%Y-%m-%d %H:%M:%S"),
        "excerpt": event_translation.description,
        "content": event_translation.description,
        "available_languages": event_translation.available_languages,
        "thumbnail": event.icon.url if event.icon else None,
        "location": location,
        "event": transform_event(event),
        "hash": None,
    }


def transform_event_recurrences(event_translation, today):
    """
    Yield all future recurrences of the event.

    :param event_translation: The event translation object which should be converted
    :type event_translation: ~integreat_cms.cms.models.events.event_translation.EventTranslation

    :param today: The first date at which event may be yielded
    :type today: ~datetime.date

    :return: An iterator over all future recurrences up to ``settings.API_EVENTS_MAX_TIME_SPAN_DAYS``
    :rtype: Iterator[:class:`~datetime.date`]
    """
    recurrence_rule = event_translation.event.recurrence_rule
    if not recurrence_rule:
        return

    # In order to avoid unnecessary computations, check if any future event
    # may be valid and return early if that is not the case
    if (
        recurrence_rule.recurrence_end_date
        and recurrence_rule.recurrence_end_date < today
    ):
        return

    event_data = transform_event_translation(event_translation)
    event_length = event_translation.event.end_date - event_translation.event.start_date

    url_base = event_data["url"][: event_data["url"].rfind("/")] + "/"
    path_base = event_data["path"][: event_data["path"].rfind("/")] + "/"

    start_date = event_translation.event.start_date
    for recurrence_date in recurrence_rule.iter_after(start_date):
        if recurrence_date - max(start_date, today) > timedelta(
            days=settings.API_EVENTS_MAX_TIME_SPAN_DAYS
        ):
            break
        if recurrence_date < today or recurrence_date == start_date:
            continue

        unique_path = generate_unique_slug(
            **{
                "slug": f"{event_translation.slug}-{recurrence_date}",
                "manager": EventTranslation.objects,
                "object_instance": event_translation,
                "foreign_model": "event",
                "region": event_translation.event.region,
                "language": event_translation.language,
            }
        )

        event_data_copy = {**event_data}
        event_data_copy["event"] = {**event_data_copy["event"]}
        event_data_copy["id"] = None
        event_data_copy["url"] = url_base + unique_path
        event_data_copy["path"] = path_base + unique_path
        event_data_copy["event"]["id"] = None
        event_data_copy["event"]["start_date"] = recurrence_date
        event_data_copy["event"]["end_date"] = recurrence_date + event_length
        yield event_data_copy


@json_response
# pylint: disable=unused-argument
def events(request, region_slug, language_slug):
    """
    List all events of the region and transform result into JSON

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the requested region
    :type region_slug: str

    :param language_slug: The slug of the requested language
    :type language_slug: str

    :return: JSON object according to APIv3 events endpoint definition
    :rtype: ~django.http.JsonResponse
    """
    region = Region.get_current_region(request)
    result = []
    now = timezone.now().date()
    for event in region.events.filter(archived=False):
        event_translation = event.get_public_translation(language_slug)
        if event_translation:
            if event.end_date >= now:
                result.append(transform_event_translation(event_translation))

            for future_event in transform_event_recurrences(event_translation, now):
                result.append(future_event)

    return JsonResponse(
        result, safe=False
    )  # Turn off Safe-Mode to allow serializing arrays
