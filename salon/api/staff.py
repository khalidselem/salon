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
    """
    Return employees that are:
      - in the given branch (if branch_id provided)
      AND
      - in EVERY service listed in service_ids (if provided)

    Response is set via frappe.response to ensure top-level JSON keys:
      frappe.response["status"], ["message"], ["data"]
    """
    try:
        site_url = frappe.utils.get_url()

        # --- collect employees in branch (if branch_id provided) ---
        branch_employees = None
        if branch_id:
            if frappe.db.exists("Branches", branch_id):
                branch_doc = frappe.get_doc("Branches", branch_id)
                branch_employees = {
                    (row.employee or "").strip() for row in getattr(branch_doc, "staff", []) if (row.employee or "").strip()
                }
            else:
                # branch not found -> no employees
                branch_employees = set()

        # --- collect employees that appear in ALL provided services ---
        employees_in_all_services = None
        service_list = [s.strip() for s in (service_ids or "").split(",") if s.strip()]
        if service_list:
            for sid in service_list:
                # try direct docname lookup first
                if not frappe.db.exists("Service", sid):
                    # try fuzzy lookup by english_name or name containing sid
                    matches = frappe.get_all("Service", filters=[["english_name", "like", f"%{sid}%"]], limit_page_length=1)
                    if matches:
                        sid_use = matches[0].name
                    else:
                        continue
                else:
                    sid_use = sid

                service_doc = frappe.get_doc("Service", sid_use)
                staff_set = {
                    (row.employee or "").strip() for row in getattr(service_doc, "staff", []) if (row.employee or "").strip()
                }

                # initialize or intersect
                if employees_in_all_services is None:
                    employees_in_all_services = staff_set
                else:
                    employees_in_all_services &= staff_set

            # if after processing services none found, ensure it's empty set
            if employees_in_all_services is None:
                employees_in_all_services = set()

        # --- compute final valid employees (AND logic) ---
        if branch_employees is not None and employees_in_all_services is not None:
            # branch provided AND services provided -> intersection
            valid_employees = branch_employees & employees_in_all_services
        elif branch_employees is not None:
            # only branch provided
            valid_employees = branch_employees
        elif employees_in_all_services is not None:
            # only services provided
            valid_employees = employees_in_all_services
        else:
            # neither provided -> no filter: return all active employees
            all_active = frappe.get_all("Employee", filters={"status": "Active"}, pluck="name")
            valid_employees = set(all_active or [])

        # If no matching employees, return empty array with correct top-level shape
        if not valid_employees:
            frappe.response["status"] = True
            frappe.response["message"] = "list fetched successfully"
            frappe.response["data"] = []
            return

        # --- fetch employee details for the valid_employees set ---
        employees = frappe.get_all(
            "Employee",
            filters={"name": ["in", list(valid_employees)], "status": "Active"},
            fields=[
                "name", "first_name", "last_name", "employee_name",
                "user_id", "cell_number", "date_of_birth",
                "gender", "date_of_joining", "image"
            ],
        )

        data = []
        for emp in employees:
            data.append({
                "id": emp.get("name"),
                "first_name": emp.get("first_name") or "",
                "last_name": emp.get("last_name") or "",
                "full_name": emp.get("employee_name") or "",
                "email": frappe.db.get_value("User", emp.get("user_id"), "email") if emp.get("user_id") else None,
                "mobile": emp.get("cell_number") or "",
                "gender": emp.get("gender") or "",
                "date_of_birth": emp.get("date_of_birth"),
                "joining_date": emp.get("date_of_joining"),
                "profile_image": f"{site_url}{emp.get('image')}" if emp.get("image") else "",
                "holiday": "Friday",
                "status": 1,
                "rating_star": 5,
            })

        # set top-level response keys (this ensures no {"message": {...}} wrapper)
        frappe.response["status"] = True
        frappe.response["message"] = "list fetched successfully"
        frappe.response["data"] = data

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_employee_list Error")
        frappe.response["status"] = False
        frappe.response["message"] = f"Server Error: {str(e)}"
        frappe.response["data"] = []