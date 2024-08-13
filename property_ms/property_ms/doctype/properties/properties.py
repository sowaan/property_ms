# Copyright (c) 2023, Sowaan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Properties(Document):
	def validate(self):
		self.validate_property_ownership()


	def validate_property_ownership(self):
		# check property ownership percentage not going over 100% and not less than 100%
		total_percentage = 0
		for row in self.ownership:
			total_percentage += row.ownership

		if total_percentage != 100:
			frappe.throw("Property Ownership Percentage must be 100%")

		# check if there is a duplicate owner
		owners = []
		for row in self.ownership:
			if row.tenant in owners:
				frappe.throw("Owner {0} is duplicated".format(row.owner))
			owners.append(row.owner)

			
