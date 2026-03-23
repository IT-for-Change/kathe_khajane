import frappe

SUPPORTED_LANGS = ["en", "kn", "mr", "ur"]

def build_app_html(icon, name):
    return f'<span class="app-ref"><img src="{icon}" width="20" height="20" class="me-1 align-middle"><strong class="ms-1">{name}</strong></span>'

def build_link_html(url, text):
    if not url:
        return ""
    return f'<a href="{url}" class="app-download ms-1"><i class="fas fa-download me-1"></i>{text}</a>'

def render_step1(text, app_html, link_html):
    if not text:
        return ""
    text = text.replace("{APP}", app_html)
    text = text.replace("{LINK}", link_html)
    return text


def get_context(context):

    lang = frappe.form_dict.get("lang", "en")
    if lang not in SUPPORTED_LANGS:
        lang = "en"

    name = frappe.db.get_value("Help Page Content", {"language_code": lang})
    doc = frappe.get_doc("Help Page Content", name)

    # ---------- ANDROID ----------
    android_app = build_app_html(
        "/files/antennapod-icon.png",
        "AntennaPod"
    )

    android_link = build_link_html(
        doc.android_install_link,
        doc.android_step1_link_text or "Download"
    )

    doc.android_step1_rendered = render_step1(
        doc.android_step1_text,
        android_app,
        android_link
    )

    # ---------- IPHONE ----------
    iphone_app = build_app_html(
        "/files/podcasts-icon.png",
        "Podcasts"
    )

    iphone_link = build_link_html(
        doc.iphone_install_link,
        doc.iphone_step1_link_text or "Download"
    )

    doc.iphone_step1_rendered = render_step1(
        doc.iphone_step1_text,
        iphone_app,
        iphone_link
    )

    # Podcast links
    all_links = frappe.get_all(
        "Podcast help",
        fields=["name","language_name","android_url","iphone_url","desktop_url","is_community","sort_order"],
        order_by="sort_order asc"
    )

    context.main_links = [l for l in all_links if not l.is_community]
    context.doc = doc
    context.no_cache = 1