from rest_framework.views import exception_handler
from rest_framework.response import Response

def payleaf_exception_handler(exc, context):
    """
    Standardizes error responses to match PayLeaf contract:
    { "error": { "type": "...", "code": "...", "message": "...", "param": "...", "request_id": "..." } }
    """
    response = exception_handler(exc, context)

    if response is not None:
        request = context.get('request')
        request_id = getattr(request, 'request_id', 'unknown') if request else 'unknown'
        
        # Handle validation error formatting
        message = response.data.get('detail')
        param = None
        
        if not message and isinstance(response.data, dict):
            # Take the first validation error if details aren't provided
            try:
                first_key = next(iter(response.data))
                first_val = response.data[first_key]
                param = first_key
                if isinstance(first_val, list):
                    message = f"{first_val[0]}"
                else:
                    message = str(first_val)
            except (StopIteration, IndexError):
                message = "Validation failed"

        status_code = response.status_code
        error_type = "api_error"
        if status_code == 400:
            error_type = "invalid_request_error"
        elif status_code in [401, 403]:
            error_type = "authentication_error"
        elif status_code == 429:
            error_type = "rate_limit_error"
        elif status_code == 404:
            error_type = "invalid_request_error"

        response.data = {
            "error": {
                "type": error_type,
                "code": getattr(exc, 'default_code', 'error'),
                "message": message or str(exc),
                "param": param,
                "request_id": request_id
            }
        }

    return response
