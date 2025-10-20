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

@frappe.whitelist(allow_guest=True)
def get_employee_list(branch_id=None, service_ids=None):
    try:
        site_url = frappe.utils.get_url()

        # Base query: only Active employees
        query = (
            frappe.qb.from_("tabEmployee")
            .select(
                "name",
                "first_name",
                "last_name",
                "employee_name",
                "user_id",
                "cell_number",
                "date_of_birth",
                "gender",
                "date_of_joining",
                "image",
                "status",
            )
            .where(Field("status") == "Active")
        )

        # Filter by branch (child table "Branches" with parent = Employee)
        if branch_id:
            branch_doc = frappe.get_doc("Branches", branch_id)
            employee_names = [row.employee for row in getattr(branch_doc, "staff", [])]
            if employee_names:
                query = query.where(Field("name").isin(employee_names))
            else:
                frappe.response["status"] = True
                frappe.response["message"] = "list fetched successfully"
                frappe.response["data"] = []
                return

        # # Filter by services (Service.doctype has child table 'staff' linking employees)
        # if service_ids:
        #     service_ids = [s.strip() for s in service_ids.split(",") if s.strip()]
        #     employees_for_services = set()
        #     for sid in service_ids:
        #         try:
        #             service_doc = frappe.get_doc("Services", sid)
        #             for row in getattr(service_doc, "staff", []):
        #                 employees_for_services.add(row.employee)
        #         except Exception:
        #             # ignore missing services
        #             pass

        #     if employees_for_services:
        #         query = query.where(Field("name").isin(list(employees_for_services)))
        #     else:
        #         frappe.response["status"] = True
        #         frappe.response["message"] = "list fetched successfully"
        #         frappe.response["data"] = []
        #         return

        # Execute
        employees = query.run(as_dict=True)
        data = []

        for emp in employees:
            data.append({
                "id": emp.get("name"),
                "first_name": emp.get("first_name"),
                "last_name": emp.get("last_name"),
                "full_name": emp.get("employee_name"),
                "email": frappe.db.get_value("User", emp.get("user_id"), "email") if emp.get("user_id") else None,
                "mobile": emp.get("cell_number"),
                "gender": emp.get("gender"),
                "date_of_birth": emp.get("date_of_birth"),
                "joining_date": emp.get("date_of_joining"),
                "profile_image": f"{site_url}{emp.get('image')}" if emp.get("image") else "",
                "holiday": "Friday",
                "status": 1,
                "rating_star": 5,
            })

        # *** IMPORTANT: set frappe.response to control top-level JSON (no "message" wrapper) ***
        frappe.response["status"] = True
        frappe.response["message"] = "list fetched successfully"
        frappe.response["data"] = data

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_employee_list Error")
        frappe.response["status"] = False
        frappe.response["message"] = f"Server Error: {str(e)}"
        frappe.response["data"] = []
