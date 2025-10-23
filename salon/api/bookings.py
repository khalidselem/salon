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

import frappe

@frappe.whitelist(allow_guest=False)
def get_available_driver(id=None, employee_id=None):
    """
    Return drivers assigned to a given state (and optionally to a specific employee)
    by checking their multiselect child tables.
    """
    try:
        if not id:
            frappe.response.update({
                "status": False,
                "message": "Missing required parameter: id (state id)",
                "data": []
            })
            return

        state_id = str(id)
        emp_id = str(employee_id) if employee_id else None

        drivers = frappe.get_all(
            "Drivers",
            fields=["name", "driver_name", "user", "device_token"]
        )

        available_drivers = []

        for d in drivers:
            driver_doc = frappe.get_doc("Drivers", d.name)

            has_state = any(
                state_id in [str(v) for v in row.as_dict().values()]
                for row in driver_doc.get("states")
            )

            has_employee = True
            if emp_id:
                has_employee = any(
                    emp_id in [str(v) for v in row.as_dict().values()]
                    for row in driver_doc.get("staff")
                )

            if has_state and has_employee:
                available_drivers.append({
                    "driver_id": d.name,
                    "driver_name": d.driver_name,
                    "user": d.user,
                    "device_token": d.device_token,
                })

        frappe.response.update({
            "status": True,
            "message": "Drivers fetched successfully",
            "data": available_drivers
        })

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Available Driver Error")
        frappe.response.update({
            "status": False,
            "message": f"Server Error: {str(e)}",
            "data": []
        })
