import frappe

# ---------------------------
# Language maps
# ---------------------------

LANG_MAP = {
    "en": "English",
    "kn": "Kannada",
    "mr": "Marathi",
    "ur": "Urdu",
}

THEME_CHILD = {
    "English": "En_theme_child",
    "Kannada": "Kn_theme_child",
    "Marathi": "Mr_theme_child",
    "Urdu": "Ur_theme_child",
}

THEME_DOCTYPE = {
    "English": "English themes",
    "Kannada": "Kannada themes",
    "Marathi": "Marathi themes",
    "Urdu": "Urdu themes",
}

# ====================================================
# DATASET BUILDER (3 DB calls total)
# ====================================================

def build_dataset(language):

    child_table = THEME_CHILD[language]
    theme_doctype = THEME_DOCTYPE[language]

    # --- DB CALL 1 ---
    stories = frappe.get_all(
        "Story",
        filters={"language": language},
        fields=[
            "name",
            "title",
            "thumbnail_image",
            "duration",
            "popular_story",
        ],
        order_by="creation desc",
    )

    # --- DB CALL 2 ---
    child_rows = frappe.get_all(
        child_table,
        fields=["parent", "linked_theme"],
    )

    # --- DB CALL 3 ---
    theme_rows = frappe.get_all(
        theme_doctype,
        fields=["name", "theme"],
    )

    theme_lookup = {t.name: t.theme for t in theme_rows}

    story_theme_map = {}

    for r in child_rows:
        story_theme_map.setdefault(r.parent, []).append(r.linked_theme)

    all_themes = set()
    top_stories = []

    for s in stories:

        linked = story_theme_map.get(s.name, [])

        s["themes"] = [
            theme_lookup.get(t)
            for t in linked
            if theme_lookup.get(t)
        ]

        all_themes.update(s["themes"])

        if s.get("popular_story"):
            top_stories.append(s)

    top_stories = sorted(top_stories, key=lambda x: x.title)[:5]

    return {
        "stories": stories,
        "themes": sorted(all_themes),
        "top_stories": top_stories,
    }

# ====================================================
# CACHE WRAPPER
# ====================================================

def get_cached_dataset(language):

    key = f"story_dataset::{language}"

    cached = frappe.cache().get_value(key)

    if cached:
        return cached

    data = build_dataset(language)

    frappe.cache().set_value(
        key,
        data,
        expires_in_sec=900,  # 15 minutes
    )

    return data

# ====================================================
# PAGE CONTROLLER
# ====================================================

def get_context(context):

    # Language selection
    lang = frappe.form_dict.get("lang", "en")
    language = LANG_MAP.get(lang, "English")

    # Filters
    raw_themes = frappe.form_dict.get("theme")

    if not raw_themes:
        selected_themes = []
    elif isinstance(raw_themes, list):
        selected_themes = raw_themes
    else:
        selected_themes = [raw_themes]

    selected_duration = frappe.form_dict.get("duration")

    # Cached dataset
    data = get_cached_dataset(language)

    filtered = []

    for s in data["stories"]:

        themes = s.get("themes", [])

        # Theme filter
        if selected_themes:
            if not all(t in themes for t in selected_themes):
                continue

        # Duration filter
        d = float(s.duration or 0)

        if selected_duration == "short" and d >= 3:
            continue

        if selected_duration == "medium" and not (3 <= d <= 5):
            continue

        if selected_duration == "long" and d <= 5:
            continue

        filtered.append(s)

    # Context to template
    context.lang = lang
    context.stories = filtered
    context.themes = data["themes"]
    context.top_stories = data["top_stories"]
    context.selected_themes = selected_themes
    context.selected_duration = selected_duration
