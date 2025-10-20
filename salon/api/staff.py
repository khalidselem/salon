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
from frappe.query_builder import Field

def log_error(title, error):
    frappe.log_error(frappe.get_traceback(), title)

def flatten(lis):
    for item in lis:
        if isinstance(item, Iterable) and not isinstance(item, str):
            for x in flatten(item):
                yield x
        else:        
            yield item

from frappe.query_builder import Field
import frappe

import frappe

@frappe.whitelist(allow_guest=True)
def get_employee_list(branch_id=None, service_ids=None):
    try:
        site_url = frappe.utils.get_url()

        # Collect employee names from Branch staff table
        employee_names = set()

        # --- Filter by branch ---
        if branch_id:
            if frappe.db.exists("Branches", branch_id):
                branch_doc = frappe.get_doc("Branches", branch_id)
                for row in getattr(branch_doc, "staff", []):
                    if row.employee:
                        employee_names.add(row.employee)

        # --- Filter by service(s) ---
        if service_ids:
            service_list = [s.strip() for s in service_ids.split(",") if s.strip()]
            for sid in service_list:
                if frappe.db.exists("Service", sid):
                    service_doc = frappe.get_doc("Service", sid)
                    for row in getattr(service_doc, "staff", []):
                        if row.employee:
                            employee_names.add(row.employee)

        # If nothing found, return empty
        if not employee_names:
            frappe.response["status"] = True
            frappe.response["message"] = "list fetched successfully"
            frappe.response["data"] = []
            return

        # Fetch Employees
        employees = frappe.get_all(
            "Employee",
            filters={"name": ["in", list(employee_names)], "status": "Active"},
            fields=[
                "name", "first_name", "last_name", "employee_name",
                "user_id", "cell_number", "date_of_birth",
                "gender", "date_of_joining", "image", "status"
            ],
        )

        # Format output
        data = []
        for emp in employees:
            data.append({
                "id": emp.name,
                "first_name": emp.first_name,
                "last_name": emp.last_name,
                "full_name": emp.employee_name,
                "email": frappe.db.get_value("User", emp.user_id, "email") if emp.user_id else None,
                "mobile": emp.cell_number,
                "gender": emp.gender,
                "date_of_birth": emp.date_of_birth,
                "joining_date": emp.date_of_joining,
                "profile_image": f"{site_url}{emp.image}" if emp.image else "",
                "holiday": "Friday",
                "status": 1,
                "rating_star": 5,
            })

        # ✅ Return final response (flat)
        frappe.response["status"] = True
        frappe.response["message"] = "list fetched successfully"
        frappe.response["data"] = data

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_employee_list Error")
        frappe.response["status"] = False
        frappe.response["message"] = f"Server Error: {str(e)}"
        frappe.response["data"] = []

