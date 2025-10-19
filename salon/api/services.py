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

@frappe.whitelist(allow_guest=True, methods=["GET"])
def category_list():
    try:
        site_url = frappe.utils.get_url()

        categories = frappe.get_all(
            "Categories",
            filters={"disable": 0, "is_group": 1},
            fields=["name", "name_english", "name_arabic", "is_group", "image", "parent_categories"]
        ) 

        category_list = []
        for c in categories:
            category_list.append({
                "id": c.name,
                "name": c.name_english or "",
                "name_arabic": c.name_arabic or "",
                "parent_id": None,
                "status": 1,
                "category_image": f"{site_url}{c.image}" if c.image else "",
                "is_gift": 0
            })

        frappe.response["status"] = True
        frappe.response["message"] = "Categories fetched successfully"
        frappe.response["data"] = category_list

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Categories Detail Error")
        frappe.response["status"] = False
        frappe.response["message"] = f"Server Error: {str(e)}"
        frappe.response["data"] = {}   

@frappe.whitelist(allow_guest=True, methods=["GET"])
def subcategory_list(parent_id=0):
    try:
        site_url = frappe.utils.get_url()

        categories = frappe.get_all(
            "Categories",
            filters={"disable": 0, "is_group": 0, "parent_categories": parent_id},
            fields=["name", "name_english", "name_arabic", "is_group", "image", "parent_categories"]
        )

        category_list = []
        for c in categories:
            category_list.append({
                "id": c.name,
                "name": c.name_english or "",
                "name_arabic": c.name_arabic or "",
                "parent_id": c.parent_categories or None,
                "status": 1,
                "category_image": f"{site_url}{c.image}" if c.image else "",
                "is_gift": 0
            })

        frappe.response["status"] = True
        frappe.response["message"] = "Sub-Categories fetched successfully"
        frappe.response["data"] = category_list

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Sub-Categories Detail Error")
        frappe.response["status"] = False
        frappe.response["message"] = f"Server Error: {str(e)}"
        frappe.response["data"] = {}  