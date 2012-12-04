from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils.dates import WEEKDAYS

import eav
from eav.models import BaseAttribute, BaseValue, EnumValue, EnumGroup, Entity

from versionutils import versioning
from pages.models import Page


class PageLink(models.Model):
    page_name = models.CharField(max_length=255, blank=True, null=True)


class WeeklySchedule(models.Model):
    """
    Has many WeeklyTimeBlock.
    """
    pass


WEEKDAY_CHOICES = [(str(n), d) for n, d in WEEKDAYS.items()]


class WeeklyTimeBlock(models.Model):
    week_day = models.CharField(max_length=1, choices=WEEKDAY_CHOICES,
        blank=False, null=False)
    start_time = models.TimeField(blank=False, null=False)
    end_time = models.TimeField(blank=False, null=False)

    schedule = models.ForeignKey(WeeklySchedule, blank=False, null=False,
        related_name='time_blocks')

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError('Starting time should be before ending time')

    def week_day_name(self):
        return WEEKDAYS[int(self.week_day)]


class PageAttribute(BaseAttribute):
    TYPE_PAGE = 'page'
    TYPE_SCHEDULE = 'schedule'


class CommentMixin(object):
    """
    Versioning-related mixin for adding a comment to a model instance on save.
    If a comment has already been set higher up the chain, it will not be
    changed.
    Override get_save_comment() to return a comment string.
    """
    def get_save_comment(self):
        return None

    def save(self, *args, **argv):
        save_with = getattr(self, "_save_with", {})
        if not "comment" in save_with:
            comment = self.get_save_comment()
            if comment is not None:
                save_with["comment"] = comment
                setattr(self, "_save_with", save_with)
        # versioning doesn't work with mixins, uncomment when fixed 
        #super(CommentMixin, self).save(*args, **argv)


class PageValue(BaseValue): ## workaround, mixin should be first
    attribute = models.ForeignKey(PageAttribute, db_index=True,
        verbose_name=_(u"attribute"))
    entity = models.ForeignKey(Page, blank=False, null=False)

    value_page = models.OneToOneField(PageLink, blank=True,
        null=True, verbose_name=_(u"page link"), related_name='eav_value')
    value_schedule = models.OneToOneField(WeeklySchedule, blank=True,
        null=True, verbose_name=_(u"weekly schedule"),
        related_name='eav_value')

    ## workaround for versionutils not working with model mixins
    #def save(self, *args, **kwargs):
    #    CommentMixin.save(self, *args, **kwargs)
    #    BaseValue.save(self, *args, **kwargs)

    def get_save_comment(self):
        return u"%s %s" % (_(u"Updated"), self.attribute.name)


class EntityAsOf(Entity):
    """
    Reconstructs an entity's attribute values as of the given date or version.
    """
    def __init__(self, instance, date=None, version=None):
        super(EntityAsOf, self).__init__(instance)
        attribute_cls = instance._eav_config_cls.attribute_cls
        value_cls = instance._eav_config_cls.value_cls
        self.all_versions = value_cls.versions.filter(entity__id=instance.id)
        if version is not None:
            date = self._version_to_date(version)
        versions_before_date = self.all_versions.filter(history_date__lte=date)
        self.version_number = len(versions_before_date)
        self.version_info = versions_before_date[0].version_info
        for a in attribute_cls.objects.all():
            try:
                value = versions_before_date.filter(attribute=a)[0:1].get()
                self.eav_attributes[a.slug] = value
            except versions_before_date.model.DoesNotExist:
                pass

    def _version_to_date(self, version):
        v = self.all_versions.order_by('history_date')[int(version) - 1]
        return v.history_date

    def __getitem__(self, name):
        return self.eav_attributes[name]

    def revert_to(self, **kwargs):
        '''
        Reverts all of this Entity's values to the versions currently selected.
        '''
        map(lambda value: value.revert_to(**kwargs),
            self.eav_attributes.values())


eav.register(Page, PageAttribute, PageValue)

versioning.register(EnumGroup)
versioning.register(EnumValue)
versioning.register(PageLink)
versioning.register(WeeklySchedule)
versioning.register(WeeklyTimeBlock)
versioning.register(PageAttribute)
versioning.register(PageValue)

# register diffs and feeds
import diff
import feeds
