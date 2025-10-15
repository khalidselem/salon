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
def dashboard_detail():
    try:
        site_url = frappe.utils.get_url()

        sliders = frappe.get_all(
            "Slider",
            filters={"disabled": 0},
            fields=["name", "slider_name", "image"]
        )

        slider_list = []
        for s in sliders:
            slider_list.append({
                "name": s.slider_name or "",
                "slider_image": f"{site_url}{s.image}" if s.image else ""
            })

        categories = frappe.get_all(
            "Categories",
            filters={"disabled": 0},
            fields=["name", "name_english", "name_arabic", "is_group", "image"]
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

        response_data = {
            "category": category_list,
            "slider": slider_list
        }

        return {
            "status": True,
            "message": "Dashboard details fetched successfully",
            "data": response_data
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Dashboard Detail Error")
        return {
            "status": False,
            "message": f"Server Error: {str(e)}",
            "data": {}
        }            