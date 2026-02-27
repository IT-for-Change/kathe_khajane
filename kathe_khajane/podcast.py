import frappe
from frappe.utils import get_url
from datetime import datetime
from xml.sax.saxutils import escape
from werkzeug.wrappers import Response
import re


# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------

BASE_URL = "http://kkdev.localhost:8082"
RTL_LANGS = ["Urdu"]


# ---------- THEMES ----------
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


# ---------- TAGS ----------
TAG_CHILD = {
    "English": "En_tag_child",
    "Kannada": "Kn_tag_child",
    "Marathi": "Mr_tag_child",
    "Urdu":    "Ur_tag_child",
}

TAG_DOCTYPE = {
    "English": "English tags",
    "Kannada": "Kannada tags",
    "Marathi": "Marathi tags",
    "Urdu":    "Urdu tags",
}


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def safe(val):
    return val or ""


def clean_html(html):
    if not html:
        return ""
    html = re.sub(r'\r', '', html)
    return html.strip()


def format_duration(d):
    if not d:
        return "00:00"
    try:
        d = str(d)
        if "." in d:
            mins, secs = d.split(".")
            return f"{int(mins):02d}:{int(secs):02d}"
        return d
    except:
        return "00:00"


# ---------------------------------------------------------
# THEMES
# ---------------------------------------------------------

def get_story_themes(story_name, language):

    child_table = THEME_CHILD.get(language)
    theme_doctype = THEME_DOCTYPE.get(language)

    if not child_table:
        return []

    rows = frappe.get_all(child_table,
        filters={"parent": story_name},
        fields=["linked_theme"]
    )

    names = [r.linked_theme for r in rows]

    if not names:
        return []

    themes = frappe.get_all(theme_doctype,
        filters={"name": ["in", names]},
        fields=["theme"]
    )

    return [t.theme for t in themes]


# ---------------------------------------------------------
# TAGS
# ---------------------------------------------------------

def get_story_tags(story_name, language):

    child_table = TAG_CHILD.get(language)
    tag_doctype = TAG_DOCTYPE.get(language)

    if not child_table:
        return []

    rows = frappe.get_all(child_table,
        filters={"parent": story_name},
        fields=["linked_tag"]
    )

    names = [r.linked_tag for r in rows]

    if not names:
        return []

    tags = frappe.get_all(tag_doctype,
        filters={"name": ["in", names]},
        fields=["tag"]
    )

    return [t.tag for t in tags]


# ---------------------------------------------------------
# PODCAST FEED
# ---------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def generate(docname):

    storycast = frappe.get_doc("Storycast", docname)

    items_xml = ""

    for row in storycast.story:

        if not row.linked_story:
            continue

        story = frappe.get_doc("Story", row.linked_story)

        # THEMES + TAGS
        themes = ", ".join(get_story_themes(story.name, story.language))
        tags   = ", ".join(get_story_tags(story.name, story.language))

        # DESCRIPTION
        story_text = safe(story.story_description)
        see_more   = getattr(story, "more_resources", "") or ""

        description_html = f"""
{story_text}
<p><strong>Themes:</strong> {themes}</p>
<p><strong>Tags:</strong> {tags}</p>
<p><a href="{see_more}">Story activity page</a></p>
"""

        if story.language in RTL_LANGS:
            description_html = f'<div dir="rtl">{description_html}</div>'

        # AUDIO + IMAGE
        audio_url = get_url(story.story_audio) if story.story_audio else ""
        image_url = get_url(story.thumbnail_image) if story.thumbnail_image else ""

        pub_date = story.creation.strftime("%a, %d %b %Y %H:%M:%S GMT")

        items_xml += f"""
<item>
<title>{escape(safe(story.title))}</title>
<enclosure url="{audio_url}" type="audio/mpeg"/>
<guid>{audio_url}</guid>
<pubDate>{pub_date}</pubDate>
<description><![CDATA[{clean_html(description_html)}]]></description>
<itunes:image href="{image_url}"/>
<itunes:duration>{format_duration(story.duration)}</itunes:duration>
</item>
"""

    # CHANNEL DESCRIPTION
    channel_desc = safe(storycast.description)

    if storycast.language in RTL_LANGS:
        channel_desc = f'<div dir="rtl">{channel_desc}</div>'

    rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
 xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">

<channel>
<title>Kathe Khajane - {storycast.language}</title>
<link>{BASE_URL}</link>
<description><![CDATA[{clean_html(channel_desc)}]]></description>
<language>en-us</language>
<itunes:author>IT for Change</itunes:author>
<itunes:explicit>false</itunes:explicit>
<itunes:image href="{get_url(storycast.thumbnail_image)}"/>
<lastBuildDate>{datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")}</lastBuildDate>

{items_xml}

</channel>
</rss>
"""

    return Response(rss_xml, mimetype="text/xml")