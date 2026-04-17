from rest_framework.throttling import SimpleRateThrottle

class BasePayLeafThrottle(SimpleRateThrottle):
    """
    Base throttle that tracks stats for X-RateLimit headers.
    """
    def parse_rate(self, rate):
        if rate is None:
            return (None, None)
        num, period = rate.split('/')
        num_requests = int(num)
        # Custom handling for '10s' or similar
        if period.endswith('s') and len(period) > 1 and period[:-1].isdigit():
            return (num_requests, int(period[:-1]))
        return super().parse_rate(rate)

    def allow_request(self, request, view):
        if self.rate is None:
            return True

        self.key = self.get_cache_key(request, view)
        if self.key is None:
            return True

        self.history = self.cache.get(self.key, [])
        self.now = self.timer()

        # Drop out-of-window requests
        while self.history and self.history[-1] <= self.now - self.duration:
            self.history.pop()

        # Store info for headers (use underlying request for middleware visibility)
        underlying_request = getattr(request, '_request', request)
        if not hasattr(underlying_request, '_ratelimit_info'):
            underlying_request._ratelimit_info = []

        remaining = self.num_requests - len(self.history) - 1
        reset = int(self.duration - (self.now - self.history[-1])) if self.history else self.duration

        underlying_request._ratelimit_info.append({
            'limit': self.num_requests,
            'remaining': max(0, remaining),
            'reset': int(reset)
        })

        if len(self.history) >= self.num_requests:
            return self.throttle_failure()
        
        return self.throttle_success()

class ApiKeyRateThrottle(BasePayLeafThrottle):
    """100 requests per 10 seconds per API Key."""
    scope = 'api_key'
    rate = '100/10s'

    def get_cache_key(self, request, view):
        if not request.auth or not hasattr(request.auth, 'id'):
            return None
        return self.cache_format % {
            'scope': self.scope,
            'ident': f"key_{request.auth.id}"
        }

class PublicIPRateThrottle(BasePayLeafThrottle):
    """1000 requests per minute per IP for public endpoints."""
    scope = 'public_ip'
    rate = '1000/min'

    def get_cache_key(self, request, view):
        # Only apply to unauthenticated or public paths
        is_authenticated = getattr(request.user, 'is_authenticated', False)
        if is_authenticated and not request.auth:
            # Session user - usually less restrictive or handled separately
            return None
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request)
        }
