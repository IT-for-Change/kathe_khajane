import frappe

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

    # --------------------------
    # Get story name from URL
    # --------------------------

    name = frappe.form_dict.get("name")

    if not name:
        frappe.throw("Story not found")

    # --------------------------
    # DB call 1 — fetch story
    # (includes description)
    # --------------------------

    story = frappe.get_doc("Story", name)

    child_table = THEME_CHILD[story.language]
    theme_doctype = THEME_DOCTYPE[story.language]

    # --------------------------
    # DB call 2 — theme links
    # --------------------------

    rows = frappe.get_all(
        child_table,
        filters={
            "parent": story.name,
            "parenttype": "Story",
        },
        fields=["linked_theme"],
    )

    theme_ids = [r.linked_theme for r in rows if r.linked_theme]

    # --------------------------
    # DB call 3 — theme labels
    # --------------------------

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

    # --------------------------
    # Send to template
    # --------------------------

    context.story = story
    context.themes = themes
    context.lang_code = LANG_CODE_MAP.get(story.language, "en")
