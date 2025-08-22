import frappe
from erpnext.accounts.doctype.journal_entry.journal_entry import JournalEntry
from frappe import _

class OverrideJournalEntry(JournalEntry):
    def submit(self):
        if len(self.accounts) > 100:
            self.db_update_all()
            self.set("__unsaved", 0)

            frappe.msgprint(_("The task has been enqueued as a background job."), alert=True)
            self.queue_action("submit", timeout=4600)
        else:
            return self._submit()
