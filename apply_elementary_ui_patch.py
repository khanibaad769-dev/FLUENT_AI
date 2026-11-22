from pathlib import Path
views_path = Path("learning/views.py")
template_path = Path("learning/templates/learning_path.html")

old_views = '''        module["total_levels"] = 15
        module["completed_levels"] = completed
        module["progress_percent"] = round(
            (completed / 15) * 100,
            1
        )'''
new_views = '''        total_levels = lessons.count()
        total_stages = lessons.values("stage_number").distinct().count()
        module["total_levels"] = total_levels
        module["total_stages"] = total_stages
        module["completed_levels"] = completed
        module["progress_percent"] = round(
            (completed / total_levels) * 100,
            1
        ) if total_levels else 0'''

if not views_path.exists() or not template_path.exists():
    raise SystemExit(
        "Run this script from the Django project folder containing manage.py."
    )

views_text = views_path.read_text(encoding="utf-8")
if new_views not in views_text:
    if old_views not in views_text:
        raise SystemExit(
            "Expected progress block was not found in learning/views.py. "
            "No files were changed."
        )
    views_path.write_text(views_text.replace(old_views, new_views, 1), encoding="utf-8")
    print("Updated learning/views.py")
else:
    print("learning/views.py already has dynamic lesson counts")

template_text = template_path.read_text(encoding="utf-8")
old_label = "3 Stages • 15 Levels"
new_label = "{{ module.total_stages }} Stages • {{ module.total_levels }} Levels"
if new_label in template_text:
    print("learning_path.html already has dynamic lesson counts")
elif old_label in template_text:
    template_path.write_text(template_text.replace(old_label, new_label, 1), encoding="utf-8")
    print("Updated learning/templates/learning_path.html")
else:
    raise SystemExit(
        "Expected stage/level label was not found in learning_path.html. "
        "Check the template manually."
    )

print("Elementary progress display patch completed.")
