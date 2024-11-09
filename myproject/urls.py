"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# main project's urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),  # Admin panel URL
    path('', RedirectView.as_view(url='/ownership/login/')),  # Redirect root URL to login page
    path('ownership/', include('ownership.urls')),  # Include URLs from the 'ownership' app
]
# myproject/urls.py
from django.contrib import admin
from django.urls import path, include

# myproject/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),  # Admin URL
    path('ownership/', include('ownership.urls')),  # Include the app's URL patterns
]
# myproject/urls.py
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

# Redirect the root URL ("/") to "ownership/login/"
def root_redirect(request):
    return redirect('login')  # Name of the 'login' view in your 'ownership' app

urlpatterns = [
    path('admin/', admin.site.urls),           # Admin page
    path('', root_redirect),                  # Root path will redirect to 'login'
    path('ownership/', include('ownership.urls')),  # Include your app's URLs
]
