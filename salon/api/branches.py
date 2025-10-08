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
def branch_list(per_page=100, page=1):
    try:
        per_page = int(per_page)
        page = int(page)
        start = (page - 1) * per_page

        # Define filters properly
        filters = {"disabled": 0}

        # Fetch branches that are not disabled
        branches = frappe.get_all(
            "Branches",
            filters=filters,
            fields=[
                "name as id",
                "name1 as name",
                "branch_for",
                "contact_number",
                "image as branch_image"
            ],
            limit_start=start,
            limit_page_length=per_page
        )

        # Build full data list for Flutter
        data = []
        for b in branches:
            branch_data = {
                "id": b.id,
                "name": b.name,
                "branch_for": b.branch_for or "",
                "contact_number": b.contact_number or "",
                "branch_image": frappe.utils.get_url(b.branch_image) if b.branch_image else "",
                "rating_star": 5,
                "total_review": 0,
                "address_line_1": "",
                "latitude": 0,
                "longitude": 0,
                "slug": b.name.lower().replace(" ", "-"),
                "status": 1,
                "description": "",
                "working_days": [],
                "payment_method": []
            }
            data.append(branch_data)

        # ✅ This part is key — no return, just assign
        frappe.response["status"] = True
        frappe.response["message"] = "branch list"
        frappe.response["data"] = data

    except Exception as e:
        frappe.log_error(message=frappe.get_traceback(), title="Branch List Error")
        frappe.response["status"] = False
        frappe.response["message"] = f"Server Error: {str(e)}"
        frappe.response["data"] = []