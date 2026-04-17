import logging
from django.conf import settings
from .models import AuditLog

try:
    from django.contrib.gis.geoip2 import GeoIP2
except ImportError:
    GeoIP2 = None

try:
    from user_agents import parse as parse_ua
except ImportError:
    parse_ua = None

logger = logging.getLogger(__name__)

class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Continue with request
        response = self.get_response(request)

        # We log mutating requests after completion to capture result
        if request.method in ('POST', 'PATCH', 'PUT', 'DELETE'):
            try:
                self.process_audit_log(request, response)
            except Exception as e:
                logger.error(f"Failed to write audit log: {e}", exc_info=True)

        return response

    def process_audit_log(self, request, response):
        # Resolve actor
        user = getattr(request, 'user', None)
        actor_id = None
        actor_type = 'system'
        actor_email = None

        if user and user.is_authenticated:
            actor_id = getattr(user, 'prefixed_id', str(user.id))
            actor_type = 'user'
            actor_email = user.email
        
        # Check for API Key auth (which we'll implement in Step 4)
        if hasattr(request, 'api_key'):
            actor_id = request.api_key.id
            actor_type = 'api_key'
            # actor_email might stay None or use merchant email

        # IP Address
        ip = self.get_client_ip(request)
        
        # User Agent & Device
        ua_string = request.META.get('HTTP_USER_AGENT', '')
        device = "unknown"
        if parse_ua:
            user_agent = parse_ua(ua_string)
            device = f"{user_agent.browser.family} on {user_agent.os.family}"
        
        # GeoIP
        geo_city = None
        geo_country = None
        if GeoIP2:
            try:
                g = GeoIP2()
                city_data = g.city(ip)
                geo_city = city_data.get('city')
                geo_country = city_data.get('country_name')
            except Exception:
                pass # GeoIP database not found or IP not in DB

        # Action: format as verb.resource
        # We can extract resource from resolver_match or use a default
        app_name = "unknown"
        view_name = "unknown"
        if request.resolver_match:
            app_name = request.resolver_match.app_name or request.resolver_match.namespace or "unknown"
            view_name = request.resolver_match.view_name or "unknown"
        
        action = f"{view_name}"
        
        # Resource ID: look for standard identifier keywords in URL
        resource_id = None
        if request.resolver_match:
            kwargs = request.resolver_match.kwargs
            resource_id = kwargs.get('id') or kwargs.get('pk') or kwargs.get('uuid') or kwargs.get('slug')

        AuditLog.objects.create(
            actor_id=actor_id,
            actor_type=actor_type,
            actor_email=actor_email,
            action=action,
            resource_type=app_name,
            resource_id=str(resource_id) if resource_id else None,
            ip=ip,
            user_agent=ua_string,
            geo_city=geo_city,
            geo_country=geo_country,
            device=device,
            result='success' if 200 <= response.status_code < 400 else 'failure',
            metadata={
                "status_code": response.status_code,
                "path": request.path,
                "method": request.method,
            }
        )

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Respect X-Forwarded-For (typically first IP is client)
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
