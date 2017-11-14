import attr
from django.conf import settings
from django.utils.http import urlencode

from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from openedx.core.djangoapps.theming.helpers import get_current_site


DEFAULT_CAMPAIGN_SOURCE = 'ace'
DEFAULT_CAMPAIGN_MEDIUM = 'email'


@attr.s
class CampaignTrackingInfo(object):
    source = attr.ib(default=DEFAULT_CAMPAIGN_SOURCE)
    medium = attr.ib(default=DEFAULT_CAMPAIGN_MEDIUM)
    campaign = attr.ib(default=None)
    term = attr.ib(default=None)
    content = attr.ib(default=None)

    def to_query_string(self, existing_parameters=None):
        new_parameters = dict(existing_parameters or {})
        for attribute, value in attr.asdict(self).iteritems():
            if value is not None:
                new_parameters['utm_' + attribute] = value
        return urlencode(new_parameters)


@attr.s
class GoogleAnalyticsTrackingPixel(object):
    ANONYMOUS_USER_CLIENT_ID = 555

    site = attr.ib(default=None)
    course_id = attr.ib(default=None)

    version = attr.ib(default=1, metadata={'param_name': 'v'})
    hit_type = attr.ib(default='event', metadata={'param_name': 't'})

    campaign_source = attr.ib(default=DEFAULT_CAMPAIGN_SOURCE, metadata={'param_name': 'cs'})
    campaign_medium = attr.ib(default=DEFAULT_CAMPAIGN_MEDIUM, metadata={'param_name': 'cm'})
    campaign_name = attr.ib(default=None, metadata={'param_name': 'cn'})

    event_category = attr.ib(default='email', metadata={'param_name': 'ec'})
    event_action = attr.ib(default='edx.bi.email.opened', metadata={'param_name': 'ea'})
    event_label = attr.ib(default=None, metadata={'param_name': 'el'})

    document_path = attr.ib(default=None, metadata={'param_name': 'dp'})

    user_id = attr.ib(default=None, metadata={'param_name': 'uid'})
    client_id = attr.ib(default=ANONYMOUS_USER_CLIENT_ID, metadata={'param_name': 'cid'})

    @property
    def image_url(self):
        parameters = {}
        fields = attr.fields(self.__class__)
        for attribute in fields:
            value = getattr(self, attribute.name, None)
            if value is not None and 'param_name' in attribute.metadata:
                parameter_name = attribute.metadata['param_name']
                parameters[parameter_name] = str(value)

        tracking_id = self._get_value_from_settings("GOOGLE_ANALYTICS_ACCOUNT")
        if tracking_id is None:
            tracking_id = self._get_value_from_settings("GOOGLE_ANALYTICS_TRACKING_ID")

        if tracking_id is None:
            return None

        parameters['tid'] = tracking_id

        user_id_dimension = self._get_value_from_settings("GOOGLE_ANALYTICS_USER_ID_CUSTOM_DIMENSION")
        if user_id_dimension is not None and self.user_id is not None:
            parameter_name = 'cd{0}'.format(user_id_dimension)
            parameters[parameter_name] = self.user_id

        if self.course_id is not None and self.event_label is None:
            param_name = fields.event_label.metadata['param_name']
            parameters[param_name] = unicode(self.course_id)

        return u"https://www.google-analytics.com/collect?{params}".format(params=urlencode(parameters))

    def _get_value_from_settings(self, name):
        site = self.site
        if self.site is None:
            site = get_current_site()

        site_configuration = None
        try:
            site_configuration = getattr(site, "configuration", None)
        except SiteConfiguration.DoesNotExist:
            pass

        value_from_settings = getattr(settings, name, None)
        if site_configuration is not None:
            return site_configuration.get_value(name, default=value_from_settings)
        else:
            return value_from_settings
