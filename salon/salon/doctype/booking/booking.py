# Copyright (c) 2025, ITQAN and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Booking(Document):
    def validate(self):
        self.calculate_total()

    def calculate_total(self):
        total = 0
        for item in self.table_veds or []:
            item_total = (item.qty or 0) * (item.price or 0)
            total += item_total
        self.total = total
