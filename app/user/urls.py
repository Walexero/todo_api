from django.urls import re_path
from user import views

app_name = "user"

urlpatterns = [
    re_path("create/", views.CreateUserView.as_view(), name="create"),
    re_path("token/", views.CreateTokenView.as_view(), name="token"),
    re_path("me/", views.ManageUserView.as_view(), name="me"),
]
