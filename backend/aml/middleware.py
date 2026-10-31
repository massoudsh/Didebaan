"""
Audit Trail Middleware
Logs all API requests and important actions for audit purposes.
Writes to both log file and AuditLog model for API access.
"""
import logging
import json
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

audit_logger = logging.getLogger('aml')


def _get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip or None


class AuditTrailMiddleware(MiddlewareMixin):
    """
    Middleware to log all API requests for audit trail (file + DB).
    """
    
    def process_request(self, request):
        """Capture request for audit; store sanitized body for process_response."""
        if request.path.startswith('/static/') or request.path.startswith('/admin/'):
            return None
        
        request._audit_request_body = {}
        if request.method in ['POST', 'PUT', 'PATCH'] and request.body:
            try:
                body = json.loads(request.body.decode('utf-8'))
                sensitive_fields = ['password', 'secret', 'token', 'api_key']
                if request.path == '/api/intelligence/screen/':
                    sensitive_fields.extend(['name', 'national_id'])
                request._audit_request_body = {
                    k: v for k, v in body.items()
                    if k.lower() not in sensitive_fields
                }
            except Exception:
                pass
        
        audit_data = {
            'timestamp': timezone.now().isoformat(),
            'method': request.method,
            'path': request.path,
            'user': request.user.username if hasattr(request.user, 'username') else 'anonymous',
            'ip_address': _get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
        if request._audit_request_body:
            audit_data['request_body'] = request._audit_request_body
        audit_logger.info(f"API Request: {json.dumps(audit_data, ensure_ascii=False)}")
        return None
    
    def process_response(self, request, response):
        """Log response to file and to AuditLog model (for audit log API)."""
        if request.path.startswith('/static/') or request.path.startswith('/admin/'):
            return response
        
        audit_data = {
            'timestamp': timezone.now().isoformat(),
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'user': request.user.username if hasattr(request.user, 'username') else 'anonymous',
        }
        audit_logger.info(f"API Response: {json.dumps(audit_data, ensure_ascii=False)}")
        
        # Persist to DB for read-only audit log API
        try:
            from .models import AuditLog
            AuditLog.objects.create(
                method=request.method,
                path=request.path,
                user=request.user.username if hasattr(request.user, 'username') else 'anonymous',
                ip_address=_get_client_ip(request),
                status_code=response.status_code,
                user_agent=(request.META.get('HTTP_USER_AGENT') or '')[:500],
                request_body=getattr(request, '_audit_request_body', {}),
            )
        except Exception:
            pass  # Do not break response if audit write fails
        
        return response

