import frappe
import csv
import os
from frappe.utils import cint

LANGUAGE_CONFIG = {
    "English": {
        "theme_doctype": "English themes",
        "theme_child": "english_themes",
        "tag_doctype": "English tags",
        "tag_child": "english_tags",
    },
    "Kannada": {
        "theme_doctype": "Kannada themes",
        "theme_child": "kannada_themes",
        "tag_doctype": "Kannada tags",
        "tag_child": "kannada_tags",
    },
    "Marathi": {
        "theme_doctype": "Marathi themes",
        "theme_child": "marathi_themes",
        "tag_doctype": "Marathi tags",
        "tag_child": "marathi_tags",
    },
    "Urdu": {
        "theme_doctype": "Urdu themes",
        "theme_child": "urdu_themes",
        "tag_doctype": "Urdu tags",
        "tag_child": "urdu_tags",
    },
    "Tamil": {
        "theme_doctype": "Tamil themes",
        "theme_child": "tamil_themes",
        "tag_doctype": "Tamil tags",
        "tag_child": "tamil_tags",
    },
    "Hindi": {
        "theme_doctype": "Hindi themes",
        "theme_child": "hindi_themes",
        "tag_doctype": "Hindi tags",
        "tag_child": "hindi_tags",
    },
    "Telugu": {
        "theme_doctype": "Telugu themes",
        "theme_child": "telugu_themes",
        "tag_doctype": "Telugu tags",
        "tag_child": "telugu_tags",
    },
}

def split_csv(value):
    if not value:
        return []
    return [v.strip() for v in str(value).split(",") if v.strip()]


def get_docnames(doctype, id_field, ids):

    if not ids:
        return []

    return frappe.get_all(
        doctype,
        filters={id_field: ["in", ids]},
        pluck="name"
    )


def story_exists(title):
    return frappe.db.exists("Story", {"title": title})


def parse_duration(value):

    if not value:
        return 0

    try:
        minutes, seconds = str(value).split(".")
        return int(minutes) * 60 + int(seconds)
    except Exception:
        return 0


def create_story(row):

    # DEBUG incoming row
    frappe.log_error(str(list(row.keys())), "ROW KEYS")

    frappe.log_error(str({
        "title": row.get("title"),
        "language": row.get("field_language"),
        "duration": row.get("field_duration"),
        "themes": row.get("field_theme_s_"),
        "tags": row.get("field_tag_s_"),
        "body": row.get("body")
    }), "CREATE STORY INPUT")

    title = row.get("title")

    if not title:
        frappe.throw("Title missing")

    existing_story = story_exists(title)
    if existing_story:
        return {
            "status": "skipped",
            "reason": "already exists",
            "story": existing_story
        }

    language = row.get("field_language")

    cfg = LANGUAGE_CONFIG.get(language)

    if not cfg:
        frappe.throw(f"Unsupported language: {language}")

    theme_ids = split_csv(row.get("field_theme_s_"))
    tag_ids = split_csv(row.get("field_tag_s_"))

    frappe.log_error(str({
        "theme_ids": theme_ids,
        "tag_ids": tag_ids
    }), "PARSED IDS")

    story = frappe.new_doc("Story")

    # Basic Information
    story.title = title
    story.language = language
    story.also_available_in = row.get("field_also_available_in")

    # Recording
    story.is_it_by_community = cint(row.get("field_is_it_by_community") == "Yes")
    story.duration = parse_duration(row.get("field_duration"))

    # Story content
    story.story_description = row.get("body")
    story.more_resources = row.get("field_more_resources")

    # Release
    story.publication_date = row.get("field_publication_date")
    story.popular_story = cint(row.get("field_popular_story") == "Y")
    story.is_this_story_validated_by_dsert = cint(row.get("field_dsert_validated") == "On")

    # node_id
    story.node_id = row.get("nid")

    # Themes and Tags
    themes = get_docnames(cfg["theme_doctype"], "source_id", theme_ids)
    tags = get_docnames(cfg["tag_doctype"], "tag_id", tag_ids)

    frappe.log_error(str({
        "themes_found": themes,
        "tags_found": tags
    }), "DB LOOKUPS")

    for theme in themes:
        story.append(cfg["theme_child"], {"linked_theme": theme})

    for tag in tags:
        story.append(cfg["tag_child"], {"linked_tag": tag})

    frappe.log_error(str({
        "title": story.title,
        "language": story.language,
        "duration": story.duration,
        "description_present": bool(story.story_description),
        "themes_count": len(themes),
        "tags_count": len(tags)
    }), "STORY BEFORE INSERT")

    story.insert(ignore_permissions=True)

    frappe.db.commit()

    frappe.log_error(story.name, "STORY CREATED")

    return {
        "status": "created",
        "story": story.name
    }


@frappe.whitelist()
def import_all_story_csv():

    csv_path = frappe.get_site_path("private", "files", "stories.csv")

    frappe.log_error(csv_path, "CSV FILE PATH")

    if not os.path.exists(csv_path):
        frappe.throw("stories.csv not found in private/files")

    created = []
    skipped = []
    failed = []
    story_node_map = []

    with open(csv_path, newline="", encoding="utf-8") as f:

        reader = csv.DictReader(f)

        frappe.log_error(str(reader.fieldnames), "CSV HEADERS")

        for i, row in enumerate(reader):

            if i < 3:
                frappe.log_error(str(row), f"CSV ROW SAMPLE {i}")

            try:

                result = create_story(row)

                if result["status"] == "created":

                    created.append(result["story"])

                    story_node_map.append({
                        "story_name": result["story"],
                        "node_id": row.get("nid")
                    })

                else:
                    skipped.append(result)

            except Exception:

                failed.append({
                    "title": row.get("title"),
                    "error": frappe.get_traceback()
                })

    mapping_file = frappe.get_site_path(
        "private", "files", "stories_mapping.csv"
    )

    with open(mapping_file, "w", newline="", encoding="utf-8") as f:

        writer = csv.DictWriter(
            f,
            fieldnames=["story_name", "node_id"]
        )

        writer.writeheader()
        writer.writerows(story_node_map)

    return {
        "created": len(created),
        "skipped": len(skipped),
        "failed": len(failed)
    }