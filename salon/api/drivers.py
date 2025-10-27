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
from frappe.auth import LoginManager

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
def driver_login(email=None, password=None, device_token=None):
    try:
        if not email or not password:
            frappe.response["status"] = False
            frappe.response["message"] = "Email and password are required"
            frappe.response["data"] = {}
            return

        site_url = frappe.utils.get_url()

        login_manager = LoginManager()
        login_manager.authenticate(user=email, pwd=password)
        login_manager.post_login()

        user = frappe.get_doc("User", email)

        driver = frappe.db.get_value("Drivers", {"user": email}, ["name", "driver_name", "device_token"], as_dict=True)
        if not driver:
            frappe.response["status"] = False
            frappe.response["message"] = "No driver record linked to this user"
            frappe.response["data"] = {}
            return

        if device_token:
            frappe.db.set_value("Drivers", driver.name, "device_token", device_token)
            frappe.db.commit()

        data = {
            "id": driver.name,
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "mobile": user.mobile_no or "",
            "email": user.name or "",
            "device_token": device_token or driver.device_token or "",
            "gender": user.gender or "",
            "profile_image": f"{site_url}{user.user_image}" or "",
            "login_type": "driver"
        }

        frappe.response["status"] = True
        frappe.response["message"] = "Login successful"
        frappe.response["data"] = data

    except frappe.exceptions.AuthenticationError:
        frappe.response["status"] = False
        frappe.response["message"] = "Invalid email or password"
        frappe.response["data"] = {}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Driver Login Error")
        frappe.response["status"] = False
        frappe.response["message"] = f"Server Error: {str(e)}"
        frappe.response["data"] = {}
