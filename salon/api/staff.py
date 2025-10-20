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

import frappe

@frappe.whitelist(allow_guest=True)
def get_employee_list(branch_id=None, service_ids=None):
    try:
        site_url = frappe.utils.get_url()

        # --- Collect branch employees ---
        branch_employees = set()
        if branch_id and frappe.db.exists("Branches", branch_id):
            branch_doc = frappe.get_doc("Branches", branch_id)
            for row in getattr(branch_doc, "staff", []):
                if row.employee:
                    branch_employees.add(row.employee)

        # --- Collect employees appearing in ALL given services ---
        service_ids_list = [s.strip() for s in (service_ids or "").split(",") if s.strip()]
        employees_in_all_services = None

        if service_ids_list:
            for sid in service_ids_list:
                if not frappe.db.exists("Service", sid):
                    continue
                service_doc = frappe.get_doc("Service", sid)
                service_employees = {row.employee for row in getattr(service_doc, "staff", []) if row.employee}
                if employees_in_all_services is None:
                    employees_in_all_services = service_employees
                else:
                    employees_in_all_services = employees_in_all_services.intersection(service_employees)

        # --- Must exist in both branch AND all services ---
        if employees_in_all_services is not None:
            valid_employees = branch_employees.intersection(employees_in_all_services)
        else:
            valid_employees = branch_employees

        if not valid_employees:
            return {
                "status": True,
                "message": "list fetched successfully",
                "data": []
            }

        # --- Fetch employee details ---
        employees = frappe.get_all(
            "Employee",
            filters={"name": ["in", list(valid_employees)], "status": "Active"},
            fields=[
                "name", "first_name", "last_name", "employee_name",
                "user_id", "cell_number", "date_of_birth",
                "gender", "date_of_joining", "image"
            ],
        )

        # --- Prepare response data ---
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

        # ✅ Clean JSON response (not nested under "message")
        frappe.local.response["http_status_code"] = 200
        frappe.local.response["type"] = "json"
        frappe.local.response["message"] = None
        frappe.local.response["data"] = None

        return {
            "status": True,
            "message": "list fetched successfully",
            "data": data
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_employee_list Error")
        return {
            "status": False,
            "message": f"Server Error: {str(e)}",
            "data": []
        }
