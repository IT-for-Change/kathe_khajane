import frappe

SUPPORTED_LANGS = ["en", "kn", "mr", "ur"]

def get_context(context):
    lang = frappe.form_dict.get("lang", "en")
    if lang not in SUPPORTED_LANGS:
        lang = "en"

    name = frappe.db.get_value("About Page Content", {"language_code": lang})
    if not name:
        # Fallback to English if language doc missing
        name = frappe.db.get_value("About Page Content", {"language_code": "en"})

    doc = frappe.get_doc("About Page Content", name)
    doc.community_text = doc.community_text or ""

    context.doc = doc
    context.lang = lang
    context.no_cache = 1