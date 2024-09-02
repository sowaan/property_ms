# Copyright (c) 2023, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
from frappe.model.document import Document


class Lease(Document):

	def validate(self):
		self.validate_increment_range()

	# Function to check for overlapping ranges and invalid range
	def validate_increment_range(self):
		for i, current in enumerate(self.increment_schedule, start=1):
			if i > 1:
				previous = self.increment_schedule[i-2]
				if current.get('from') <= previous.get('to'):
					frappe.throw(f"Error: Overlapping range detected between row {i-1} and row {i}")

	def on_submit(self):
		self.unit_rented()
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
				"company": self.company,
				"custom_lease_reference": self.name,
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

	def unit_rented(self):
		for unit in self.choose_units:
			print(unit.rented, unit.unit_name, "checing values \n\n\n\n")
			# frappe.db.set_value("Choose Units", unit.name, "rented", 1)
			frappe.db.set_value("Unit", unit.unit_name, "rented", 1)

