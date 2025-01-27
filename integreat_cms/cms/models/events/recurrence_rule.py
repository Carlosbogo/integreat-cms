from datetime import date, timedelta
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _

from ...constants import frequency, weekdays, weeks


class RecurrenceRule(models.Model):
    """
    Data model representing the recurrence frequency and interval of an event
    """

    #: Manage choices in :mod:`~integreat_cms.cms.constants.frequency`
    frequency = models.CharField(
        max_length=7,
        choices=frequency.CHOICES,
        default=frequency.WEEKLY,
        verbose_name=_("frequency"),
        help_text=_("How often the event recurs"),
    )
    interval = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_("Repeat every ... time(s)"),
        help_text=_("The interval in which the event recurs."),
    )
    #: Manage choices in :mod:`~integreat_cms.cms.constants.weekdays`
    weekdays_for_weekly = ArrayField(
        models.IntegerField(choices=weekdays.CHOICES),
        blank=True,
        verbose_name=_("weekdays"),
        help_text=_(
            "If the frequency is weekly, this field determines on which days the event takes place"
        ),
    )
    #: Manage choices in :mod:`~integreat_cms.cms.constants.weekdays`
    weekday_for_monthly = models.IntegerField(
        choices=weekdays.CHOICES,
        null=True,
        blank=True,
        verbose_name=_("weekday"),
        help_text=_(
            "If the frequency is monthly, this field determines on which days the event takes place"
        ),
    )
    #: Manage choices in :mod:`~integreat_cms.cms.constants.weeks`
    week_for_monthly = models.IntegerField(
        choices=weeks.CHOICES,
        null=True,
        blank=True,
        verbose_name=_("week"),
        help_text=_(
            "If the frequency is monthly, this field determines on which week of the month the event takes place"
        ),
    )
    recurrence_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("recurrence end date"),
        help_text=_(
            "If the recurrence is not for an indefinite period, this field contains the end date"
        ),
    )

    def iter_after(self, start_date):
        """
        Iterate all recurrences after a given start date.
        This method assumes that ``weekdays_for_weekly`` contains at least one member
        and that ``weekday_for_monthly`` and ``week_for_monthly`` are not null.

        :param start_date: The date on which the iteration should start
        :type start_date: ~datetime.date

        :return: An iterator over all dates defined by this recurrence rule
        :rtype: Iterator[:class:`~datetime.date`]
        """
        next_recurrence = start_date

        def get_nth_weekday(month_date, weekday, n):
            """
            Get the nth occurrence of a given weekday in a specific month

            :param month_date: the current date of month
            :type month_date: datetime.datetime

            :param weekday: the requested weekday
            :type weekday: str

            :param n: the requested number
            :type n: integer

            :return: The nth weekday
            :rtype: datetime.datetime
            """
            month_date = month_date.replace(day=1)
            month_date += timedelta((weekday - month_date.weekday()) % 7)
            return month_date + timedelta(weeks=n - 1)

        def next_month(month_date):
            """
            Advance the given date by one month

            :param month_date: the given date
            :type month_date: datetime.datetime

            :return: The same date one month later
            :rtype: datetime.datetime
            """
            if month_date.month < 12:
                return month_date.replace(month=month_date.month + 1)

            return month_date.replace(month=1, year=month_date.year + 1)

        def advance():
            """
            Get the next occurrence by this rule

            :return: date objects
            :rtype: Iterator[:class: `~datetime.date`]
            """

            nonlocal next_recurrence
            if self.frequency == frequency.DAILY:
                yield
                next_recurrence += timedelta(days=1)
            elif self.frequency == frequency.WEEKLY:
                # Yield each day of the week that is valid, since
                # ``interval`` should apply here only on weekly basis
                for weekday in sorted(self.weekdays_for_weekly):
                    if weekday < next_recurrence.weekday():
                        continue
                    next_recurrence += timedelta(
                        days=weekday - next_recurrence.weekday()
                    )
                    yield
                # advance to the next monday
                next_recurrence += timedelta(days=7 - next_recurrence.weekday())
            elif self.frequency == frequency.MONTHLY:
                next_recurrence = get_nth_weekday(
                    next_recurrence, self.weekday_for_monthly, self.week_for_monthly
                )
                if next_recurrence < start_date:
                    next_recurrence = get_nth_weekday(
                        next_month(next_recurrence),
                        self.weekday_for_monthly,
                        self.week_for_monthly,
                    )
                yield
                next_recurrence = next_month(next_recurrence)
            elif self.frequency == frequency.YEARLY:
                yield

                # It is not possible to go simply to the next year if the current date is february 29
                year_dif = 1
                while True:
                    try:
                        next_recurrence = next_recurrence.replace(
                            year=next_recurrence.year + year_dif
                        )
                        break
                    except ValueError:
                        year_dif += 1

        i = 0
        end_date = self.recurrence_end_date or date.max
        while True:
            for _ in advance():
                if next_recurrence > end_date:
                    return
                if i % self.interval == 0:
                    yield next_recurrence
            i += 1

    def __str__(self):
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``RecurrenceRule object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the recurrence rule
        :rtype: str
        """
        return ugettext('Recurrence rule of "{}" ({})').format(
            self.event.best_translation.title, self.get_frequency_display()
        )

    def __repr__(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<RecurrenceRule: RecurrenceRule object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the recurrence rule
        :rtype: str
        """
        return f"<RecurrenceRule (id: {self.id}, event: {self.event.best_translation.slug})>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("recurrence rule")
        #: The plural verbose name of the model
        verbose_name_plural = _("recurrence rules")
        #: The default permissions for this model
        default_permissions = ()
