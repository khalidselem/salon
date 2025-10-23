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

@frappe.whitelist(allow_guest=False)
def get_states(id=None):
    try:
        if not id:
            frappe.response["status"] = False
            frappe.response["message"] = "Missing required parameter: id (branch_id)"
            frappe.response["data"] = []
            return
            
        states = frappe.get_all(
            "States",
            filters={"branch": id},
            fields=["name", "state_name", "branch", "branch_name"]
        )

        frappe.response["status"] = True
        frappe.response["message"] = "States fetched successfully"
        frappe.response["data"] = states

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get States Error")
        frappe.response["status"] = False
        frappe.response["message"] = f"Server Error: {str(e)}"
        frappe.response["data"] = []

@frappe.whitelist(allow_guest=False)
def get_available_driver(id=None):
    try:
        if not id:
            frappe.response["status"] = False
            frappe.response["message"] = "Missing required parameter: id"
            frappe.response["data"] = []
            return

        drivers = frappe.get_all(
            "Drivers",
            fields=["name", "driver_name", "user", "device_token", "states"]
        )

        available_drivers = []

        for driver in drivers:
            state_records = frappe.get_all(
                "list of States table",
                filters={"parent": driver.name},
                fields=["state"]
            )

            if any(str(r.get("state")) == str(id) for r in state_records):
                available_drivers.append({
                    "driver_id": driver.name,
                    "driver_name": driver.driver_name,
                    "user": driver.user,
                    "device_token": driver.device_token,
                })

        frappe.response["status"] = True
        frappe.response["message"] = "Drivers fetched successfully"
        frappe.response["data"] = available_drivers

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Available Driver Error")
        frappe.response["status"] = False
        frappe.response["message"] = f"Server Error: {str(e)}"
        frappe.response["data"] = []

