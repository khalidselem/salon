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
def get_user(user):
    doc = frappe.get_doc("User", user)
    return {"user": doc, "type": "user"}

@frappe.whitelist(allow_guest=True)
def get_branches(filters=None):
    """
    إرجاع قائمة الفروع مع الحقول المطلوبة فقط
    """
    try:
        # لو فيه فلاتر قادمة من التطبيق
        if isinstance(filters, string_types):
            filters = json.loads(filters)

        branches = frappe.db.get_list(
            "Branches",
            filters=filters,
            fields=["name", "name1", "image", "branch_for", "assign"]
        )

        # تجهيز الصور لتكون روابط كاملة يمكن فتحها من الموبايل
        base_url = frappe.utils.get_url()  
        for branch in branches:
            if branch.get("image"):
                branch["image"] = f"{base_url}{branch['image']}"

        return {
            "status": 1,
            "count": len(branches),
            "data": branches
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Branches API Error")
        return {
            "status": 0,
            "error": str(e)
        }



