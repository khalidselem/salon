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

@frappe.whitelist(allow_guest=True)
def get_employee_list(branch_id=None, service_ids=None):
    try:
        site_url = frappe.utils.get_url()

        # --- collect employees in branch ---
        branch_employees = set()
        if branch_id and frappe.db.exists("Branches", branch_id):
            branch_doc = frappe.get_doc("Branches", branch_id)
            for row in getattr(branch_doc, "staff", []):
                if row.employee:
                    branch_employees.add(row.employee)

        # --- collect employees for each service ---
        service_employees_list = []
        if service_ids:
            service_list = [s.strip() for s in service_ids.split(",") if s.strip()]
            for sid in service_list:
                if frappe.db.exists("Service", sid):
                    service_doc = frappe.get_doc("Service", sid)
                    employees_for_this_service = {
                        row.employee for row in getattr(service_doc, "staff", []) if row.employee
                    }
                    if employees_for_this_service:
                        service_employees_list.append(employees_for_this_service)

        # --- calculate intersection ---
        # start with branch employees
        final_employees = branch_employees.copy() if branch_employees else set()

        if service_employees_list:
            # if branch provided, intersect with all services
            if final_employees:
                for s in service_employees_list:
                    final_employees &= s
            else:
                # if no branch, intersect among all services
                final_employees = set.intersection(*service_employees_list)

        # --- if no matching employees ---
        if not final_employees:
            frappe.response["status"] = True
            frappe.response["message"] = "list fetched successfully"
            frappe.response["data"] = []
            return

        # --- fetch employee details ---
        employees = frappe.get_all(
            "Employee",
            filters={"name": ["in", list(final_employees)], "status": "Active"},
            fields=[
                "name", "first_name", "last_name", "employee_name",
                "user_id", "cell_number", "date_of_birth",
                "gender", "date_of_joining", "image", "status"
            ],
        )

        # --- format output ---
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

        # ✅ flat response
        frappe.response["status"] = True
        frappe.response["message"] = "list fetched successfully"
        frappe.response["data"] = data

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_employee_list Error")
        frappe.response["status"] = False
        frappe.response["message"] = f"Server Error: {str(e)}"
        frappe.response["data"] = []


