import frappe
from datetime import datetime
from xml.sax.saxutils import escape
from werkzeug.wrappers import Response
import re
from urllib.parse import quote


RTL_LANGS = ["Urdu"]


# ---------------- LABEL DICTIONARIES ---------------- #

LABEL_ACTIVITY = {
    "English": '<a href="{url}">Click here</a> for story activity page',
    "Kannada": 'ಕಥೆಯ ಚಟುವಟಿಕೆ ಪುಟಕ್ಕೆ <a href="{url}">ಇಲ್ಲಿ ಕ್ಲಿಕ್ಕಿಸಿ</a>',
    "Marathi": 'स्टोरी अ‍ॅक्टिव्हिटी पेजसाठी <a href="{url}">येथे क्लिक करा</a>',
    "Urdu": '<a href="{url}">سرگرمی صفحہ</a>',
}

LABEL_TAGS = {
    "English": "Tag(s)",
    "Kannada": "ಗುರುತು ಪಟ್ಟಿ",
    "Marathi": "टॅग्ज",
    "Urdu": "ٹیگ",
}

LABEL_THEMES = {
    "English": "Theme(s)",
    "Kannada": "ಕಥಾವಸ್ತು",
    "Marathi": "थीम",
    "Urdu": "موضوع",
}


# ---------------- THEME TABLES ---------------- #

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


# ---------------- TAG TABLES ---------------- #

TAG_CHILD = {
    "English": "En_tag_child",
    "Kannada": "Kn_tag_child",
    "Marathi": "Mr_tag_child",
    "Urdu": "Ur_tag_child",
}

TAG_DOCTYPE = {
    "English": "English tags",
    "Kannada": "Kannada tags",
    "Marathi": "Marathi tags",
    "Urdu": "Urdu tags",
}


# ---------------- HELPERS ---------------- #

def safe(val):
    return val or ""


def clean_html(html):
    if not html:
        return ""

    html = re.sub(r'\r', '', html)

    html = re.sub(
        r'<div[^>]*class="[^"]*ql-editor[^"]*"[^>]*>(.*?)</div>',
        r'\1',
        html,
        flags=re.DOTALL
    )

    return html.strip()


def format_duration(seconds):

    if not seconds:
        return "00:00"

    try:
        total = int(float(str(seconds)))
        mins = total // 60
        secs = total % 60
        return f"{mins:02d}:{secs:02d}"
    except Exception:
        return "00:00"


def build_activity_link(language, url):

    template = LABEL_ACTIVITY.get(language, LABEL_ACTIVITY["English"])

    if "{url}" in template:
        return template.format(url=url or "")

    return f'<a href="{url or ""}">Story activity page</a>'


# ---------------- FETCH THEMES ---------------- #

def get_story_themes(story_name, language):

    child_table = THEME_CHILD.get(language)
    theme_doctype = THEME_DOCTYPE.get(language)

    if not child_table:
        return []

    rows = frappe.get_all(
        child_table,
        filters={"parent": story_name},
        fields=["linked_theme"]
    )

    names = [r.linked_theme for r in rows if r.linked_theme]

    if not names:
        return []

    themes = frappe.get_all(
        theme_doctype,
        filters={"name": ["in", names]},
        fields=["theme"]
    )

    return [t.theme for t in themes]


# ---------------- FETCH TAGS ---------------- #

def get_story_tags(story_name, language):

    child_table = TAG_CHILD.get(language)
    tag_doctype = TAG_DOCTYPE.get(language)

    if not child_table:
        return []

    rows = frappe.get_all(
        child_table,
        filters={"parent": story_name},
        fields=["linked_tag"]
    )

    names = [r.linked_tag for r in rows if r.linked_tag]

    if not names:
        return []

    tags = frappe.get_all(
        tag_doctype,
        filters={"name": ["in", names]},
        fields=["tag"]
    )

    return [t.tag for t in tags]


# ---------------- RSS FEED GENERATOR ---------------- #

@frappe.whitelist(allow_guest=True)
def generate(docname):

    storycast = frappe.get_doc("Storycast", docname)

    config = frappe.get_single("Podcast Config")

    BASE_URL = safe(config.base_url).rstrip("/")
    WEBSITE_LINK = safe(config.website_link)

    language = safe(storycast.language) or "Kannada"

    items_xml = ""


    for row in storycast.story:

        if not row.linked_story:
            continue

        story = frappe.get_doc("Story", row.linked_story)

        lang = safe(story.language) or language


        themes_list = get_story_themes(story.name, lang)
        tags_list = get_story_tags(story.name, lang)

        themes_str = ", ".join(themes_list)
        tags_str = ", ".join(tags_list)

        lbl_themes = LABEL_THEMES.get(lang, "Themes")
        lbl_tags = LABEL_TAGS.get(lang, "Tags")


        story_text = clean_html(safe(story.story_description))


        activity_url = safe(getattr(story, "more_resources", "")) or ""

        activity_url = re.sub(
            r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>.*?</a>',
            r'\1',
            activity_url,
            flags=re.DOTALL
        ).strip()


        activity_link_html = build_activity_link(lang, activity_url)


        description_parts = [story_text]

        if themes_str:
            description_parts.append(
                f"<br><strong>{lbl_themes}</strong>: {themes_str}"
            )

        if tags_str:
            description_parts.append(
                f"<br><strong>{lbl_tags}</strong>: {tags_str}"
            )

        description_parts.append(f"<br>{activity_link_html}")

        description_html = "\n".join(description_parts)

        if lang in RTL_LANGS:
            description_html = f'<div dir="rtl">{description_html}</div>'


        audio_url = ""

        if story.story_audio:
            audio_url = BASE_URL + quote(story.story_audio)


        image_url = ""

        if story.thumbnail_image:
            image_url = BASE_URL + quote(story.thumbnail_image)


        pub_date_raw = getattr(story, "pub_date", None) or story.creation

        if hasattr(pub_date_raw, "strftime"):
            pub_date = pub_date_raw.strftime("%Y-%m-%dT%H:%M:%S")
        else:
            pub_date = str(pub_date_raw)


        duration_str = format_duration(getattr(story, "duration", 0))


        items_xml += f"""
<item>
<title>{escape(safe(story.title))}</title>
<enclosure url="{audio_url}" type="audio/mpeg"/>
<pubDate>{pub_date}</pubDate>
<description><![CDATA[{clean_html(description_html)}]]></description>
<itunes:image href="{image_url}"/>
<itunes:duration>{duration_str}</itunes:duration>
</item>
"""


    channel_title = safe(getattr(storycast, "title", "")) or safe(storycast.name)

    channel_desc = clean_html(safe(storycast.description))

    if language in RTL_LANGS:
        channel_desc = f'<div dir="rtl">{channel_desc}</div>'


    channel_image = ""

    if storycast.thumbnail_image:
        channel_image = BASE_URL + quote(storycast.thumbnail_image)


    storycast_id = safe(getattr(storycast, "podcast_id", "")) or safe(storycast.name)

    copyright_txt = safe(getattr(storycast, "copyright_text", "")) or "CC BY-NC-ND 4.0"

    itunes_author = safe(getattr(storycast, "itunes_author", "")) or "Kathe Khajane Team"


    rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>

<rss version="2.0"
 xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">

<channel>

<title>{escape(channel_title)}</title>

<link>{WEBSITE_LINK}</link>

<description><![CDATA[{channel_desc}]]></description>

<copyright>{escape(copyright_txt)}</copyright>

<itunes:author>{escape(itunes_author)}</itunes:author>

<itunes:image href="{channel_image}"/>

<lastBuildDate>{datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")}</lastBuildDate>

<id>{storycast_id}</id>

{items_xml}

</channel>
</rss>
"""

    return Response(rss_xml, mimetype="text/xml")