# Copyright (c) 2023, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
from frappe.model.document import Document


class Lease(Document):

	def before_save(self):
		if self.docstatus == 0:
			for unit in self.choose_units:
				unit.rented = 1

	def on_submit(self):
		self.rented()
		for payment in self.payments_scheduling:
			rate_wo_tax = flt(payment.total_amount) - flt(payment.total_tax)
			rate = rate_wo_tax if self.ex_tax_on_add_char == 0 else rate_wo_tax - payment.additional_charges
			if self.ex_tax_on_add_char == 1:
				for item in self.taxes:
					if item.charge_type == "Actual":
						item.tax_amount = payment.additional_charges
						item.rate = 0
			
			invoice = frappe.get_doc({
				"doctype": "Sales Invoice",
				"customer": self.renter,
				"posting_date": payment.issued_date,
				"due_date": payment.due_date,
				"taxes_and_charges": self.taxes_and_charges,
				"taxes": self.taxes,
			})

			for tenant in self.property_ownership:
				invoice.append("items", {
					"item_code": self.item,
					"qty": 1,
					"rate": rate * (tenant.ownership / 100),
					"cost_center": tenant.cost_center,	
				})
			invoice.save()
			# invoice.submit()

	def rented(self):
		for unit in self.choose_units:
			unit_doc = frappe.get_doc("Unit", unit.unit_name)
			unit_doc.rented = 1
			unit.rented = 1
			unit_doc.save()

