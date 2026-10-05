from frappe.model.document import Document


class KCSettings(Document):
    def on_update(self):
        from kayanick_crm.settings import clear_cache

        clear_cache()
