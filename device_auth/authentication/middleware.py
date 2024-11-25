import hashlib
from django.core.cache import cache
from django.http import JsonResponse
import hashlib

class DeviceAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Identify the device
        user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
        ip_address = request.META.get('REMOTE_ADDR', '')
        device_id = hashlib.sha256(f"{user_agent}-{ip_address}".encode()).hexdigest()
        request.device_id = device_id

        # Check cache for device authorization
        cache_key = f"allowed_device:{device_id}"
        is_allowed = cache.get(cache_key)

        if is_allowed is None:
            # Fallback: Check the database if the device is allowed
            from authentication.models import Device
            device = Device.objects.filter(device_id=device_id, is_trusted=True).first()
            if device:
                cache.set(cache_key, True, timeout=86400)  # Cache for 24 hours
                is_allowed = True
            else:
                is_allowed = False

        if not is_allowed:
            return JsonResponse({"message": "Device not authorized."}, status=403)

        return self.get_response(request)
