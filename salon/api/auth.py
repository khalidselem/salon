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
        # Parse incoming JSON
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
            frappe.response["status"] = False
            frappe.response["message"] = "Email is required"
            frappe.response["data"] = {}
            return

        # Try to find existing user by email
        user_name = frappe.db.get_value("User", {"email": email}, "name")

        if user_name:
            user = frappe.get_doc("User", user_name)
            # Update login_type if empty
            if not user.login_type:
                user.login_type = login_type
                user.save(ignore_permissions=True)

            frappe.response["status"] = True
            frappe.response["message"] = "login success"
            frappe.response["data"] = _user_to_dict(user)
            return

        # Create new user if not found
        full_name = f"{first_name or ''} {last_name or ''}".strip()

        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "full_name": full_name,
            "enabled": 1,
            "user_type": "Website User",
            "login_type": login_type,
        })
        user.insert(ignore_permissions=True)

        # Save profile image if available
        if profile_image:
            try:
                file = frappe.get_doc({
                    "doctype": "File",
                    "file_url": profile_image,
                    "attached_to_doctype": "User",
                    "attached_to_name": user.name,
                })
                file.insert(ignore_permissions=True)
            except Exception as img_err:
                frappe.log_error(f"Profile image save error: {img_err}", "Social Login")

        frappe.response["status"] = True
        frappe.response["message"] = "user created"
        frappe.response["data"] = _user_to_dict(user)

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Social Login Error")
        frappe.response["status"] = False
        frappe.response["message"] = f"Server Error: {str(e)}"
        frappe.response["data"] = {}


def _user_to_dict(user):
    """Return user info in Flutter-friendly format"""
    file_url = frappe.db.get_value("File", {"attached_to_doctype": "User", "attached_to_name": user.name}, "file_url")

    return {
        "id": user.name,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "login_type": user.login_type,
        "full_name": user.full_name,
        "profile_image": frappe.utils.get_url(file_url) if file_url else "",
        "created_at": str(user.creation),
        "updated_at": str(user.modified),
    }



