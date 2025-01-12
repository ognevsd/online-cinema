import http
import json
import logging
from enum import StrEnum, auto

import requests

# from django.conf import settings
from config import settings
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class Roles(StrEnum):
    ADMIN = "admin"
    SUPERUSER = "superuser"
    SUBSCRIBER = auto()


logger = logging.getLogger(__name__)


class CustomBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        url = f"{settings.AUTH_API_LOGIN_URL}/login"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        payload = {"username": username, "password": password}
        response = requests.post(url, headers=headers, data=payload)
        if response.status_code != http.HTTPStatus.OK:
            return None

        data = response.json()

        access_token = data.get("access_token")

        url = f"{settings.AUTH_API_LOGIN_URL}/get-details"
        headers = {"authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers)
        if response.status_code != http.HTTPStatus.OK:
            return None

        data = response.json()
        user_roles = []

        for role in data["roles"]:
            user_roles.append(role["name"])

        try:
            user, _ = User.objects.get_or_create(
                id=data["id"],
            )
            user.login = data.get("login")
            user.first_name = data.get("first_name")
            user.last_name = data.get("last_name")
            if Roles.ADMIN in user_roles or Roles.SUPERUSER in user_roles:
                user.is_admin = True
                user.is_staff = True
            user.save()
        except Exception:
            return None

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
