from django.shortcuts import render

# Create your views here.
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from .models import Device

from django.core.cache import cache

def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        device_id = getattr(request, 'device_id', None)
        
        user = authenticate(request, username=username, password=password)
        if user:
            device, created = Device.objects.get_or_create(user=user, device_id=device_id)
            if not device.is_trusted:
                return JsonResponse({"message": "Untrusted device. Please verify."}, status=403)
            
            # Log the user in
            login(request, user)
            device.last_active_at = now()
            device.save()

            # Update the cache
            cache_key = f"allowed_device:{device_id}"
            cache.set(cache_key, True, timeout=86400)

            return JsonResponse({"message": "Logged in successfully."})
        
        return JsonResponse({"message": "Invalid credentials."}, status=401)
    return JsonResponse({"message": "Invalid request method."}, status=400)


from django.core.mail import send_mail

def register_device_view(request):
    if request.method == "POST":
        user = request.user
        device_id = getattr(request, 'device_id', None)
        device_name = request.POST.get('device_name', 'Unknown Device')

        if device_id:
            device, created = Device.objects.get_or_create(user=user, device_id=device_id)
            if created or not device.is_trusted:
                device.device_name = device_name
                device.is_trusted = False
                device.save()
                
                # Send verification email or OTP
                send_mail(
                    'Device Verification',
                    'Please confirm this device to trust it.',
                    'noreply@example.com',
                    [user.email],
                    fail_silently=False,
                )
                return JsonResponse({"message": "Device registered. Please verify."}, status=201)
        
        return JsonResponse({"message": "Device already trusted."})
    return JsonResponse({"message": "Invalid request method."}, status=400)

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def list_devices(request):
    if request.user.is_authenticated:
        devices = Device.objects.filter(user=request.user)
        data = [{"id": d.id, "name": d.device_name, "trusted": d.is_trusted} for d in devices]
        return JsonResponse({"devices": data}, safe=False)
    return JsonResponse({"message": "Unauthorized"}, status=401)

@csrf_exempt
def revoke_device(request, device_id):
    if request.user.is_authenticated:
        try:
            device = Device.objects.get(user=request.user, id=device_id)
            cache_key = f"allowed_device:{device.device_id}"
            cache.delete(cache_key)  # Remove device from cache
            device.delete()
            return JsonResponse({"message": "Device revoked."})
        except Device.DoesNotExist:
            return JsonResponse({"message": "Device not found."}, status=404)
    return JsonResponse({"message": "Unauthorized"}, status=401)

