from datetime import datetime, time, date
from dateutil.rrule import weekday, rrule

from django.db import models
from django.db.models import Q
from django.utils.translation import get_language, ugettext_lazy as _

from ...constants import frequency, status
from ...utils.slug_utils import generate_unique_slug
from ..media.media_file import MediaFile
from ..pois.poi import POI
from ..regions.region import Region, Language
from .recurrence_rule import RecurrenceRule


class EventQuerySet(models.QuerySet):
    """
    Custom QuerySet to facilitate the filtering by date while taking recurring events into account.
    """

    def filter_upcoming(self, from_date=date.today()):
        """
        Filter all events that take place after the given date. This is, per definition, if at least one of the
        following conditions is true:

            * The end date of the event is the given date or later
            * The event is indefinitely recurring
            * The event is recurring and the recurrence end date is the given date or later

        :param from_date: The date which should be used for filtering, defaults to the current date
        :type from_date: datetime.date

        :return: The Queryset of events after the given date
        :rtype: ~integreat_cms.cms.models.events.event.EventQuerySet
        """
        return self.filter(
            Q(end_date__gte=from_date)
            | Q(
                recurrence_rule__isnull=False,
                recurrence_rule__recurrence_end_date__isnull=True,
            )
            | Q(
                recurrence_rule__isnull=False,
                recurrence_rule__recurrence_end_date__gte=from_date,
            )
        )

    def filter_completed(self, to_date=date.today()):
        """
        Filter all events that are not ongoing and don't have any occurrences in the future. This is, per definition, if
        at least one of the following conditions is true:

            * The event is non-recurring and the end date of the event is before the given date
            * The event is recurring and the recurrence end date is before the given date

        :param to_date: The date which should be used for filtering, defaults to the current date
        :type to_date: datetime.date

        :return: The Queryset of events before the given date
        :rtype: ~integreat_cms.cms.models.events.event.EventQuerySet
        """
        return self.filter(
            Q(recurrence_rule__isnull=True, end_date__lt=to_date)
            | Q(
                recurrence_rule__isnull=False,
                recurrence_rule__recurrence_end_date__lt=to_date,
            )
        )


class Event(models.Model):
    """
    Data model representing an event.
    Can be directly imported from :mod:`~integreat_cms.cms.models`.
    """

    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name=_("region"),
    )
    location = models.ForeignKey(
        POI,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="events",
        verbose_name=_("location"),
    )
    start_date = models.DateField(verbose_name=_("start date"))
    start_time = models.TimeField(blank=True, verbose_name=_("start time"))
    end_date = models.DateField(verbose_name=_("end date"))
    end_time = models.TimeField(blank=True, verbose_name=_("end time"))
    #: If the event is recurring, the recurrence rule contains all necessary information on the frequency, interval etc.
    #: which is needed to calculate the single instances of a recurring event
    recurrence_rule = models.OneToOneField(
        RecurrenceRule,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name=_("recurrence rule"),
    )
    icon = models.ForeignKey(
        MediaFile,
        verbose_name=_("icon"),
        on_delete=models.SET_NULL,
        related_name="icon_events",
        blank=True,
        null=True,
    )
    archived = models.BooleanField(default=False, verbose_name=_("archived"))

    #: The default manager
    objects = EventQuerySet.as_manager()

    @property
    def languages(self):
        """
        This property returns a QuerySet of all :class:`~integreat_cms.cms.models.languages.language.Language` objects, to which an event
        translation exists.

        :return: QuerySet of all :class:`~integreat_cms.cms.models.languages.language.Language` an event is translated into
        :rtype: ~django.db.models.query.QuerySet [ ~integreat_cms.cms.models.languages.language.Language ]
        """
        return Language.objects.filter(event_translations__event=self)

    @property
    def is_recurring(self):
        """
        This property checks if the event has a recurrence rule and thereby determines, whether the event is recurring.

        :return: Whether the event is recurring or not
        :rtype: bool
        """
        return bool(self.recurrence_rule)

    @property
    def is_all_day(self):
        """
        This property checks whether an event takes place the whole day by checking if start time is minimal and end
        time is maximal.

        :return: Whether event takes place all day
        :rtype: bool
        """
        return self.start_time == time.min and self.end_time == time.max.replace(
            second=0, microsecond=0
        )

    @property
    def has_location(self):
        """
        This property checks whether the event has a physical location (:class:`~integreat_cms.cms.models.pois.poi.POI`).

        :return: Whether event has a physical location
        :rtype: bool
        """
        return bool(self.location)

    def get_translation(self, language_slug):
        """
        This function uses the reverse foreign key ``self.translations`` to get all translations of ``self``
        and filters them to the requested :class:`~integreat_cms.cms.models.languages.language.Language` slug.

        :param language_slug: The slug of the desired :class:`~integreat_cms.cms.models.languages.language.Language`
        :type language_slug: str

        :return: The event translation in the requested :class:`~integreat_cms.cms.models.languages.language.Language` or :obj:`None`
                 if no translation exists
        :rtype: ~integreat_cms.cms.models.events.event_translation.EventTranslation
        """
        return self.translations.filter(language__slug=language_slug).first()

    def get_occurrences(self, start, end):
        """
        Get occurrences of the event that overlap with ``[start, end]``.
        Expects ``start < end``.

        :param start: the begin of the requested interval.
        :type start: ~datetime.datetime

        :param end: the end of the requested interval.
        :type end: ~datetime.datetime

        :return: start datetimes of occurrences of the event that are in the given timeframe
        :rtype: list [ ~datetime.datetime ]
        """
        event_start = datetime.combine(
            self.start_date, self.start_time if self.start_time else time.min
        )
        event_end = datetime.combine(
            self.end_date, self.end_time if self.end_time else time.max
        )
        event_span = event_end - event_start
        recurrence = self.recurrence_rule
        if recurrence is not None:
            until = min(
                end,
                datetime.combine(
                    recurrence.recurrence_end_date
                    if recurrence.recurrence_end_date
                    else date.max,
                    time.max,
                ),
            )
            if recurrence.frequency in (frequency.DAILY, frequency.YEARLY):
                occurrences = rrule(
                    recurrence.frequency,
                    dtstart=event_start,
                    interval=recurrence.interval,
                    until=until,
                )
            elif recurrence.frequency == frequency.WEEKLY:
                occurrences = rrule(
                    recurrence.frequency,
                    dtstart=event_start,
                    interval=recurrence.interval,
                    byweekday=recurrence.weekdays_for_weekly,
                    until=until,
                )
            else:
                occurrences = rrule(
                    recurrence.frequency,
                    dtstart=event_start,
                    interval=recurrence.interval,
                    byweekday=weekday(
                        recurrence.weekday_for_monthly, recurrence.week_for_monthly
                    ),
                    until=until,
                )
            return [
                x
                for x in occurrences
                if start <= x <= end or start <= x + event_span <= end
            ]
        return (
            [event_start]
            if start <= event_start <= end or start <= event_end <= end
            else []
        )

    def get_public_translation(self, language_slug):
        """
        This function retrieves the newest public translation of an event.

        :param language_slug: The slug of the requested :class:`~integreat_cms.cms.models.languages.language.Language`
        :type language_slug: str

        :return: The public translation of an event
        :rtype: ~integreat_cms.cms.models.events.event_translation.EventTranslation
        """
        return self.translations.filter(
            language__slug=language_slug,
            status=status.PUBLIC,
        ).first()

    @property
    def backend_translation(self):
        """
        This function returns the translation of this event in the current backend language.

        :return: The backend translation of a event
        :rtype: ~integreat_cms.cms.models.events.event_translation.EventTranslation
        """
        return self.translations.filter(language__slug=get_language()).first()

    @property
    def default_translation(self):
        """
        This function returns the translation of this event in the region's default language.
        Since an event can only be created by creating a translation in the default language, this is guaranteed to return
        an event translation.

        :return: The default translation of an event
        :rtype: ~integreat_cms.cms.models.events.event_translation.EventTranslation
        """
        return self.translations.filter(language=self.region.default_language).first()

    @property
    def best_translation(self):
        """
        This function returns the translation of this event in the current backend language and if it doesn't exist, it
        provides a fallback to the translation in the region's default language.

        :return: The "best" translation of an event for displaying in the backend
        :rtype: ~integreat_cms.cms.models.events.event_translation.EventTranslation
        """
        return self.backend_translation or self.default_translation

    def duplicate(self, user):
        """
        This method creates a copy of this event and all of its translations.
        This method saves the new event.

        :param user: The user who initiated this copy
        :type user: ~django.contrib.auth.models.User

        :return: A copy of this event
        :rtype: ~integreat_cms.cms.models.events.event.Event
        """
        # save all translations on the original object, so that they can be duplicated later
        translations = list(self.translations.all())

        # Clear the own recurrence rule.
        # If the own recurrence rule would not be cleared, django would throw an
        # error that the recurrence rule is not unique (because it would belong to both
        # the cloned and the new object)
        recurrence_rule = self.recurrence_rule

        if recurrence_rule:
            # duplicate the recurrence rule, if it exists
            recurrence_rule.pk = None
            recurrence_rule.save()
            self.recurrence_rule = recurrence_rule

        # create the duplicated event
        self.pk = None
        self.save()

        copy_translation = _("copy")
        # Create new translations for this event
        for translation in translations:
            translation.pk = None
            translation.event = self
            translation.status = status.DRAFT
            translation.title = f"{translation.title} ({copy_translation})"
            translation.slug = generate_unique_slug(
                **{
                    "slug": translation.slug,
                    "manager": type(translation).objects,
                    "object_instance": translation,
                    "foreign_model": "event",
                    "instance": self,
                    "region": self.region,
                    "language": translation.language,
                }
            )
            translation.currently_in_translation = False
            translation.creator = user
            translation.save()

        return self

    def __str__(self):
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``Event object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the event
        :rtype: str
        """
        return self.best_translation.title

    def __repr__(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<Event: Event object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the event
        :rtype: str
        """
        return f"<Event (id: {self.id}, region: {self.region.slug}, slug: {self.best_translation.slug})>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("event")
        #: The plural verbose name of the model
        verbose_name_plural = _("events")
        #: The fields which are used to sort the returned objects of a QuerySet
        ordering = ["start_date", "start_time"]
        #: The default permissions for this model
        default_permissions = ("change", "delete", "view")
        #: The custom permissions for this model
        permissions = (("publish_event", "Can publish events"),)
