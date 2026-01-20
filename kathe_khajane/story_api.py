import frappe
import csv
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
    title = row.get("title")

    if not title:
        frappe.throw("Title is missing in CSV")

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

    story = frappe.new_doc("Story")

    story.title = title
    story.language = language
    story.also_available_in = row.get("field_also_available_in")
    story.collaborators = row.get("field_collaborator_s_")
    story.duration = parse_duration(row.get("field_duration"))
    story.story_description = row.get("body")
    story.more_resources = row.get("field_more_resources")
    story.publication_date = row.get("field_publication_date")
    story.node_id = row.get("nid")

    story.is_it_by_community = cint(row.get("field_is_it_by_community") == "Yes")
    story.is_this_story_validated_by_dsert = cint(row.get("field_dsert_validated") == "On")
    story.popular_story = cint(row.get("field_popular_story") == "Y")

    themes = get_docnames(cfg["theme_doctype"], "source_id", theme_ids)
    tags = get_docnames(cfg["tag_doctype"], "tag_id", tag_ids)

    for theme in themes:
        story.append(cfg["theme_child"], {
            "linked_theme": theme
        })

    for tag in tags:
        story.append(cfg["tag_child"], {
            "linked_tag": tag
        })

    story.insert(ignore_permissions=True)

    return {
        "status": "created",
        "story": story.name
    }

@frappe.whitelist(methods=["POST"])
def import_stories_from_csv():
    story_node_map = []

    csv_path = frappe.get_site_path("private", "marathi.csv")

    if not frappe.os.path.exists(csv_path):
        frappe.throw("stories.csv not found")
    
    created = []
    skipped = []
    failed = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
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

    if story_node_map:
        output_path = frappe.get_site_path("private", "story_node_mapping.csv")

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["story_name", "node_id"]
            )
            writer.writeheader()
            writer.writerows(story_node_map)

    return {
        "created_count": len(created),
        "skipped_count": len(skipped),
        "failed_count": len(failed),
        "created": created,
        "skipped": skipped,
        "failed": failed
    }
