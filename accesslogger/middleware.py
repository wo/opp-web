import logging
from django.conf import settings
from django.utils import timezone
from accesslogger import utils
from accesslogger.models import Visit

log = logging.getLogger('accesslogger.middleware')

class AccessLoggerMiddleware(object):
    """
    Store access record in the database
    """

    @property
    def ignore_url_prefixes(self):
        """Returns a list of url prefixes that we should not track"""
        if not hasattr(self, '_url_prefixes'):
            self._url_prefixes = getattr(settings, 'NO_STATS_URLS', [])
        return self._url_prefixes
    
    @property
    def ignore_user_agents(self):
        """Returns a list of substrings of user agents that we should not track"""
        if not hasattr(self, '_uas'):
            self._uas = getattr(settings, 'NO_STATS_USERAGENTS', [])
        return self._uas

    def process_request(self, request):
        ip_address = utils.get_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]

        for ua in self.ignore_user_agents:
            if user_agent.find(ua) != -1:
                log.debug('Not tracking UA "%s" because of keyword: %s', user_agent, ua)
                return

        for prefix in self.ignore_url_prefixes:
            if request.path.startswith(prefix):
                log.debug('Not tracking request to %s', request.path)
                return
            
        referrer = request.META.get('HTTP_REFERER', '')[:255]
        if referrer.startswith(request.get_host()):
            referrer = ''

        visit = Visit(
            date = timezone.now(),
            page = request.path,
            ip = ip_address,
            ua = user_agent,
            username = request.user.username if request.user else '',
            referrer = referrer
        )
        try:
            visit.save()
        except:
            log.error('could not save visit!')

        return None
