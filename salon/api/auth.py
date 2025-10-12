import json
import base64
import os
from collections.abc import Iterable
from six import string_types
import frappe
from frappe.utils import flt
from frappe import _
from frappe.utils import get_files_path
from frappe.utils.file_manager import save_file
from frappe.utils import nowdate, nowtime, get_first_day, getdate

def log_error(title, error):
    frappe.log_error(frappe.get_traceback(), title)

def flatten(lis):
    for item in lis:
        if isinstance(item, Iterable) and not isinstance(item, str):
            for x in flatten(item):
                yield x
        else:        
            yield item

@frappe.whitelist(allow_guest=True)
def social_login(**kwargs):
    """Handle social login (Google / Apple) from Flutter app."""
    try:
        # Parse incoming JSON data
        if frappe.request.method == "POST":
            data = json.loads(frappe.request.data)
        else:
            data = kwargs

        login_type = data.get("login_type")
        email = data.get("email")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        profile_image = data.get("profile_image")

        if not email:
            frappe.response.update({
                "status": False,
                "message": "Email is required",
                "data": {}
            })
            return

        # Try to find existing user
        user_name = frappe.db.get_value("User", {"email": email}, "name")

        if user_name:
            user = frappe.get_doc("User", user_name)

            # If bio (login_type) not set, set it now
            if not user.bio:
                user.bio = login_type

            # Update user_image if a new one is provided
            if profile_image and user.user_image != profile_image:
                user.user_image = profile_image

            user.save(ignore_permissions=True)

            frappe.response.update({
                "status": True,
                "message": "login success",
                "data": _user_to_dict(user)
            })
            return

        # If user doesn't exist, create one
        full_name = f"{first_name or ''} {last_name or ''}".strip()

        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "full_name": full_name,
            "enabled": 1,
            "bio": login_type,
            "user_type": "Website User",
            "user_image": profile_image or "",
            "send_welcome_email": 0
        })
        user.insert(ignore_permissions=True)

        frappe.response.update({
            "status": True,
            "message": "user created",
            "data": _user_to_dict(user)
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Social Login Error")
        frappe.response.update({
            "status": False,
            "message": f"Server Error: {str(e)}",
            "data": {}
        })


def _user_to_dict(user):
    """Return user info in Flutter-friendly format"""
    return {
        "id": user.name,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "login_type": user.bio,
        "full_name": user.full_name,
        "profile_image": frappe.utils.get_url(user.user_image) if user.user_image else "",
        "created_at": str(user.creation),
        "updated_at": str(user.modified),
    }

@frappe.whitelist(allow_guest=True)
def register(**kwargs):
    """Register new user (no token needed, Flutter friendly)"""
    try:
        # Parse incoming JSON data from Flutter
        if frappe.request and frappe.request.method == "POST":
            data = json.loads(frappe.request.data)
        else:
            data = kwargs

        first_name = data.get("first_name")
        last_name = data.get("last_name")
        email = data.get("email")
        password = data.get("password")
        gender = data.get("gender", "").lower()
        user_type = data.get("user_type", "email")

        # Basic validation
        if not first_name or not email or not password:
            frappe.response["status"] = False
            frappe.response["message"] = "First name, email, and password are required"
            frappe.response["data"] = {}
            return

        # Check if email already exists
        if frappe.db.exists("User", {"email": email}):
            frappe.response["status"] = False
            frappe.response["message"] = "Email already registered"
            frappe.response["data"] = {}
            return

        # Create full name
        full_name = f"{first_name or ''} {last_name or ''}".strip()

        # Create new user
        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "full_name": full_name,
            "user_type": "Website User",
            "enabled": 1,
            "gender": gender,
            "bio": user_type,
            "send_welcome_email": 0
        })
        user.insert(ignore_permissions=True)

        # Set password securely
        if password:
            frappe.db.set_value("User", user.name, "password", frappe.utils.password.encrypt(password))

        frappe.db.commit()

        # Prepare JSON response
        frappe.response["status"] = True
        frappe.response["message"] = "Register successful"
        frappe.response["data"] = _register_user_to_dict(user)

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Register API Error")
        frappe.response["status"] = False
        frappe.response["message"] = f"Server Error: {str(e)}"
        frappe.response["data"] = {}


def _register_user_to_dict(user):
    """Format user info for Flutter"""
    return {
        "id": user.name,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "gender": user.gender,
        "login_type": user.bio or "",
    }

