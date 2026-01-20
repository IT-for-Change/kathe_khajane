import frappe
@frappe.whitelist()
def update_story_media(story_name, audio=None, thumbnail=None):
    if not story_name:
        frappe.throw("story_name is required")

    story = frappe.get_doc("Story", story_name)

    if audio and not story.story_audio:
        story.story_audio = audio

    if thumbnail and not story.thumbnail_image:
        story.thumbnail_image = thumbnail

    story.save(ignore_permissions=True)

    return {"status": "ok", "story": story.name}
