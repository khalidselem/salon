import frappe
from frappe.model.document import Document

class Booking(Document):
    def validate(self):
        self.calculate_total()

    def calculate_total(self):
        total = 0
        for row in self.table_services:
            row.total_price = (row.qty or 0) * (row.price or 0)
            total += row.total_price
        self.total = total