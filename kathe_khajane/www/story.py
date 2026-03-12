import frappe
from urllib.parse import quote

# Language → child table mapping
THEME_CHILD = {
    "English": "En_theme_child",
    "Kannada": "Kn_theme_child",
    "Marathi": "Mr_theme_child",
    "Urdu": "Ur_theme_child",
}

# Language → theme master mapping
THEME_DOCTYPE = {
    "English": "English themes",
    "Kannada": "Kannada themes",
    "Marathi": "Marathi themes",
    "Urdu": "Urdu themes",
}

# Language → URL code mapping
LANG_CODE_MAP = {
    "English": "en",
    "Kannada": "kn",
    "Marathi": "mr",
    "Urdu": "ur",
}


def get_context(context):

    name = frappe.form_dict.get("name")

    if not name:
        frappe.throw("Story not found")


    story = frappe.get_doc("Story", name)

    lang_code = LANG_CODE_MAP.get(story.language, "en")
    frappe.local.lang = lang_code

    child_table = THEME_CHILD[story.language]
    theme_doctype = THEME_DOCTYPE[story.language]

    rows = frappe.get_all(
        child_table,
        filters={
            "parent": story.name,
            "parenttype": "Story",
        },
        fields=["linked_theme"],
    )

    theme_ids = [r.linked_theme for r in rows if r.linked_theme]

    theme_rows = frappe.get_all(
        theme_doctype,
        filters={"name": ["in", theme_ids]},
        fields=["name", "theme"],
    )

    theme_lookup = {t.name: t.theme for t in theme_rows}

    themes = [
        theme_lookup.get(t)
        for t in theme_ids
        if theme_lookup.get(t)
    ]

    context.story = story
    context.story.antenna_pod_url = (
        f"https://antennapod.org/deeplink/search?query={quote(story.title)}"
    )
    context.themes = themes
    context.lang_code = lang_code
    context.no_cache = 1