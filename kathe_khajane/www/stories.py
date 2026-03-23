import frappe
from urllib.parse import quote

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
    "Urdu":    "Ur_theme_child",
}

THEME_DOCTYPE = {
    "English": "English themes",
    "Kannada": "Kannada themes",
    "Marathi": "Marathi themes",
    "Urdu":    "Urdu themes",
}

def build_dataset(language):
    child_table   = THEME_CHILD[language]
    theme_doctype = THEME_DOCTYPE[language]

    stories = frappe.get_all(
        "Story",
        filters={"language": language},
        fields=["name", "title", "thumbnail_image", "duration", "popular_story"],
        order_by="creation desc",
    )

    child_rows = frappe.get_all(child_table, fields=["parent", "linked_theme"])
    theme_rows = frappe.get_all(theme_doctype, fields=["name", "theme"])

    theme_lookup    = {t.name: t.theme for t in theme_rows}
    story_theme_map = {}
    for r in child_rows:
        story_theme_map.setdefault(r.parent, []).append(r.linked_theme)

    all_themes  = set()
    top_stories = []

    for s in stories:
        linked      = story_theme_map.get(s.name, [])
        s["themes"] = [theme_lookup[t] for t in linked if theme_lookup.get(t)]
        all_themes.update(s["themes"])
        if s.get("popular_story"):
            top_stories.append(s)

    top_stories = sorted(top_stories, key=lambda x: x.title)[:5]
    return {
        "stories":     stories,
        "themes":      sorted(all_themes),
        "top_stories": top_stories,
    }

def get_cached_dataset(language):
    key    = f"story_dataset::{language}"
    cached = frappe.cache().get_value(key)
    if cached:
        return cached
    data = build_dataset(language)
    frappe.cache().set_value(key, data, expires_in_sec=900)
    return data

def get_context(context):
    lang     = frappe.form_dict.get("lang", "en")
    language = LANG_MAP.get(lang, "English")
    frappe.local.lang = lang

    # Use werkzeug MultiDict to get all selected theme values
    try:
        selected_themes = list(frappe.request.args.getlist("theme"))
    except Exception:
        raw = frappe.form_dict.get("theme")
        if not raw:
            selected_themes = []
        elif isinstance(raw, list):
            selected_themes = raw
        else:
            selected_themes = [raw]

    selected_duration = frappe.form_dict.get("duration")
    is_filtered       = bool(selected_themes or selected_duration)

    data     = get_cached_dataset(language)
    filtered = []

    for s in data["stories"]:
        themes = s.get("themes", [])
        if selected_themes and not all(t in themes for t in selected_themes):
            continue
        # duration is stored as raw minutes (e.g. 5.13) — use as-is for filtering
        d = float(s.duration or 0)
        if selected_duration == "short"  and d >= 3:            continue
        if selected_duration == "medium" and not (3 <= d <= 5): continue
        if selected_duration == "long"   and d <= 5:            continue
        filtered.append(s)

    combined_query     = "+".join(quote(t) for t in selected_themes) if selected_themes else None
    combined_deep_link = (
        f"https://antennapod.org/deeplink/search?query={combined_query}"
        if combined_query else None
    )

    context.lang               = lang
    context.stories            = filtered
    context.themes             = data["themes"]
    context.top_stories        = [] if is_filtered else data["top_stories"]
    context.selected_themes    = selected_themes
    context.selected_duration  = selected_duration
    context.combined_deep_link = combined_deep_link
    context.is_filtered        = is_filtered
    context.no_cache           = 1