from django import forms
from django.forms.models import ModelForm, inlineformset_factory,\
    ModelChoiceField
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from eav.forms import BaseDynamicEntityForm

from pages.models import Page
from infobox.models import WeeklySchedule, WeeklyTimeBlock, PageLink,\
    PageAttribute
from widgets import DateTimeWidget, TimeWidget
from django.forms.fields import TimeField


class PageLinkForm(ModelForm):
    class Meta:
        model = PageLink


class WeeklyTimeBlockForm(ModelForm):
    start_time = TimeField(label=_('From'),
                           widget=TimeWidget(scroll_default_time='9:00am'))
    end_time = TimeField(label=_('To'),
                         widget=TimeWidget(scroll_default_time='5:00pm'))

    class Meta:
        model = WeeklyTimeBlock


WeeklyTimeBlockFormSet = inlineformset_factory(WeeklySchedule, WeeklyTimeBlock,
    form=WeeklyTimeBlockForm, extra=7)


class WeeklyScheduleForm(WeeklyTimeBlockFormSet):
    def save(self, commit=True):
        if not self.instance.pk:
            self.instance.save()
        super(WeeklyScheduleForm, self).save(commit)
        # For compatibility with versioning, we save instance last.
        self.instance.save()
        return self.instance


class DateTimeField(forms.DateTimeField):
    widget = DateTimeWidget


class InfoboxForm(BaseDynamicEntityForm):
    CUSTOM_FIELD_CLASSES = {
        'date': DateTimeField,
        'schedule': WeeklyScheduleForm,
        'page': PageLinkForm,
    }

    def get_field_class_for_type(self, type):
        return BaseDynamicEntityForm.get_field_class_for_type(self, type)

    def save(self, commit=True):
        # we don't want to save the model instance, just the EAV attributes
        super(InfoboxForm, self).save(commit=False)
        self.entity.save()


class AddAttributeForm(ModelForm):
    attribute = ModelChoiceField(queryset=PageAttribute.objects.all())

    def __init__(self, *args, **kwargs):
        # we want to exclude attributes the entity already has
        super(AddAttributeForm, self).__init__(*args, **kwargs)
        self.entity = self.instance.eav
        already_has = [v.attribute.pk for v in self.entity.get_values()]
        self.fields['attribute'].queryset = PageAttribute.objects.exclude(
                                                            pk__in=already_has)

    def save(self, commit=False):
        attribute = self.cleaned_data.get('attribute', None)
        attribute.save_value(self.entity.model, None)


class AttributeCreateForm(ModelForm):
    class Meta:
        model = PageAttribute
        fields = ('name', 'description', 'type', 'enum_group')
        exclude = ('site', 'slug')

    def save(self, *args, **kwargs):
        # tie attributes to Page model on save
        self.instance.parent = ContentType.objects.get_for_model(Page)
        return super(AttributeCreateForm, self).save(*args, **kwargs)


class AttributeUpdateForm(ModelForm):
    class Meta:
        model = PageAttribute
        fields = ('name', 'description')
