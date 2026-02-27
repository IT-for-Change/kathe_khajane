import frappe
from kathe_khajane.www.help import build_app_html, build_link_html, render_step1

def get_context(context):
    name = frappe.db.get_value("Help Page Content", {"language_code": "en"})
    if not name:
        frappe.throw("English help content missing")

    doc = frappe.get_doc("Help Page Content", name)

    # Override title and subtitle
    doc.title    = "How to access Kathe Khajane community podcasts"
    doc.subtitle = "Follow these simple steps to access and subscribe to the Kathe Khajane community stories podcasts on your device"

    # ---------- ANDROID ----------
    android_app  = build_app_html("/assets/kathe_khajane/images/antennapod-icon.png", "AntennaPod")
    android_link = build_link_html(doc.android_install_link, doc.android_step1_link_text or "Download")
    doc.android_step1_rendered = render_step1(doc.android_step1_text, android_app, android_link)

    # ---------- IPHONE ----------
    iphone_app  = build_app_html("/assets/kathe_khajane/images/podcasts-icon.png", "Podcasts")
    iphone_link = build_link_html(doc.iphone_install_link, doc.iphone_step1_link_text or "Download")
    doc.iphone_step1_rendered = render_step1(doc.iphone_step1_text, iphone_app, iphone_link)

    # ---------- DESKTOP ----------
    gpodder_app = build_app_html("/assets/kathe_khajane/images/gpodder-icon.png", "gPodder")
    doc.desktop_step1_rendered = render_step1(doc.desktop_step1_text, gpodder_app, "")

    doc.community_feeds_text = doc.community_feeds_text or ""

    # Community links only
    links = frappe.get_all(
        "Podcast help",
        filters={"is_community": 1},
        fields=["language_name", "android_url", "iphone_url", "desktop_url", "sort_order"],
        order_by="sort_order asc"
    )

    context.main_links      = links
    context.community_links = []
    context.doc             = doc
    context.lang            = "en"
    context.community_mode  = True