import hashlib
import json
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse

class IdempotencyMiddleware:
    """
    Ensures that requests with the same Idempotency-Key return the same response.
    Stores (key, body_hash, response) in Redis for 24h.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # We only care about mutating requests
        if request.method not in ('POST', 'PATCH', 'PUT'):
            return self.get_response(request)

        idempotency_key = request.META.get('HTTP_IDEMPOTENCY_KEY')
        if not idempotency_key:
            return self.get_response(request)

        # Hash request body for consistency check
        # Note: reading request.body might be expensive for large payloads, 
        # but standard for idempotency.
        body_hash = hashlib.sha256(request.body).hexdigest()
        cache_key = f"idempotency:{idempotency_key}"
        
        cached_data = cache.get(cache_key)
        if cached_data:
            if cached_data['hash'] != body_hash:
                return JsonResponse({
                    "error": {
                        "code": "idempotency_error",
                        "message": "Idempotency-Key reuse with different request body."
                    }
                }, status=400)
            
            # Reconstruct response from cache
            response = HttpResponse(
                json.dumps(cached_data['response']),
                content_type="application/json",
                status=cached_data['status']
            )
            response['X-Idempotency-Replay'] = 'true'
            return response

        # Proceed with request
        response = self.get_response(request)
        
        # Only cache if not a server error
        if response.status_code < 500 and response.get('Content-Type') == 'application/json':
            try:
                # Ensure content is available (render if it's a DRF Response)
                if hasattr(response, 'render') and callable(response.render):
                    response.render()
                
                content_json = json.loads(response.content)
                
                cache.set(cache_key, {
                    'hash': body_hash,
                    'status': response.status_code,
                    'response': content_json
                }, timeout=86400) # 24 hours
            except (ValueError, Exception):
                pass

        return response

class RequestIDMiddleware:
    """
    Ensures every request has a unique X-Request-Id header.
    Reads from incoming headers if present, otherwise generates a UUID.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        import uuid
        request_id = request.META.get('HTTP_X_REQUEST_ID', str(uuid.uuid4()))
        request.request_id = request_id
        
        response = self.get_response(request)
        response['X-Request-Id'] = request_id
        return response

class RateLimitHeaderMiddleware:
    """
    Returns X-RateLimit-* headers based on DRF throttling info.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        if hasattr(request, '_ratelimit_info') and request._ratelimit_info:
            # Pick the most restrictive (lowest remaining)
            info = min(request._ratelimit_info, key=lambda x: x['remaining'])
            response['X-RateLimit-Limit'] = str(info['limit'])
            response['X-RateLimit-Remaining'] = str(info['remaining'])
            response['X-RateLimit-Reset'] = str(info['reset'])
            
        return response
