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
def get_available_driver(id=None, employee_id=None):
    """
    Return drivers who:
      - have `state` == id in child table "list of States table"
      - AND have `employee` == employee_id in child table "Employee Select Table"
    Parameters:
      id (state id) and employee_id (Employee docname)
    """
    try:
        if not id:
            frappe.response["status"] = False
            frappe.response["message"] = "Missing required parameter: id (state id)"
            frappe.response["data"] = []
            return

        # Normalize to string for comparisons (child table values are stored as strings/docnames)
        state_id = str(id)
        emp_id = str(employee_id) if employee_id else None

        # Fetch drivers basic info
        drivers = frappe.get_all(
            "Drivers",
            fields=["name", "driver_name", "user", "device_token"]
        )

        available_drivers = []

        for d in drivers:
            driver_name = d.get("name")

            # Check state child table for this driver
            has_state = frappe.db.exists(
                "list of States table",
                {"parent": driver_name, "state": state_id}
            )

            if not has_state:
                # skip driver if they don't serve the state
                continue

            # If employee_id was provided, check that driver has that employee in their staff
            if emp_id:
                has_employee = frappe.db.exists(
                    "Employee Select Table",
                    {"parent": driver_name, "employee": emp_id}
                )
                if not has_employee:
                    continue  # driver doesn't deliver that employee -> skip

            # Passed both checks -> include driver
            available_drivers.append({
                "name": driver_name,
                "driver_name": d.get("driver_name"),
                "user": d.get("user"),
                "device_token": d.get("device_token"),
            })

        frappe.response["status"] = True
        frappe.response["message"] = "Drivers fetched successfully"
        frappe.response["data"] = available_drivers
        return

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Available Driver Error")
        frappe.response["status"] = False
        frappe.response["message"] = f"Server Error: {str(e)}"
        frappe.response["data"] = []
        return