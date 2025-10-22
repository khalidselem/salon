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


@frappe.whitelist(allow_guest=True)
def service_list(category_id=None, subcategory_id=None, search=None, branch_id=None):
    try:
        site_url = frappe.utils.get_url()

        # Base filters
        filters = {"disabled": 0}
        services = frappe.get_all(
            "Service",
            fields=[
                "name",
                "english_name",
                "arabic_name",
                "english_description",
                "arabic_description",
                "price",
                "duration",
                "category",
                "subcategory",
                "image",
                "branches",
                "gift",
            ],
            filters=filters,
            order_by="creation desc"
        )

        # 🔍 Filter by category and subcategory
        if category_id:
            services = [s for s in services if s.get("category") == category_id]

        if subcategory_id:
            services = [s for s in services if s.get("subcategory") == subcategory_id]

        # 🏢 Filter by branch (MultiSelect)
        if branch_id:
            filtered = []
            for s in services:
                if not s.get("branches"):
                    continue
                try:
                    branches = frappe.parse_json(s.get("branches"))
                except Exception:
                    branches = [s.get("branches")]
                if branch_id in branches:
                    filtered.append(s)
                    
            services = filtered

        # 🔍 Search in Arabic + English names
        if search:
            search_lower = search.lower()
            services = [
                s for s in services
                if search_lower in (s.get("english_name") or "").lower()
                or search_lower in (s.get("arabic_name") or "").lower()
            ]

        # 🧩 Format for Flutter
        formatted = []
        for s in services:
            formatted.append({
                "id": s.get("name"),
                "name": s.get("english_name"),
                "name_ar": s.get("arabic_name"),
                "description_en": s.get("english_description"),
                "description_ar": s.get("arabic_description"),
                "default_price": s.get("price"),
                "duration_min": s.get("duration"),
                "category_id": s.get("category"),
                "status": 1,
                "sub_category_id": s.get("subcategory"),
                "service_image": f"{site_url}{s['image']}" if s.get("image") else None,
                "is_gift_category": s.get("gift"), 
            })

        return {
            "status": True,
            "message": "service list fetched successfully",
            "data": formatted
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Service List Error")
        return {
            "status": False,
            "message": f"Server Error: {e}",
            "data": []
        }

@frappe.whitelist(allow_guest=True)
def service_list(category_id=None, subcategory_id=None, search=None, branch_id=None):
    try:
        site_url = frappe.utils.get_url()
        
        services = frappe.get_all(
            "Service",
            fields=[
                "name",
                "english_name",
                "arabic_name",
                "english_description",
                "arabic_description",
                "price",
                "duration",
                "category",
                "subcategory",
                "image",
                "disabled",
            ],
            filters={"disabled": 0},
            order_by="creation desc"
        )

        filtered_services = []

        for s in services:
            if branch_id:
                branch_links = frappe.get_all(
                    "Branches",
                    filters={"parent": s.name},
                    fields=["branch"]
                )
                branch_ids = [b.branch for b in branch_links]

                if branch_id not in branch_ids:
                    continue

            if category_id and s.get("category") != category_id:
                continue
            if subcategory_id and s.get("subcategory") != subcategory_id:
                continue

            if search:
                term = search.lower()
                if term not in (s.get("english_name") or "").lower() and \
                   term not in (s.get("arabic_name") or "").lower():
                    continue

            filtered_services.append({
                "id": s.get("name"),
                "name": s.get("english_name"),
                "name_ar": s.get("arabic_name"),
                "description_en": s.get("english_description"),
                "description_ar": s.get("arabic_description"),
                "default_price": s.get("price"),
                "duration_min": s.get("duration"),
                "category_id": s.get("category"),
                "status": 1,
                "sub_category_id": s.get("subcategory"),
                "service_image": f"{site_url}{s['image']}" if s.get("image") else None,
                "is_gift_category": 0
            })

        frappe.response["status"] = True
        frappe.response["message"] = "service list fetched successfully"
        frappe.response["data"] = filtered_services

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Service List Error")
        frappe.response["status"] = False
        frappe.response["message"] = f"Server Error: {e}"
        frappe.response["data"] = []
