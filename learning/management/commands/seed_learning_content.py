import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from learning.models import Lesson, Quiz, Question

class Command(BaseCommand):
    help = "Import Elementary, Intermediate and Advanced Fluent AI content."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        path = Path(__file__).resolve().parents[2] / "data" / "elementary_intermediate_advanced.json"
        if not path.exists():
            raise CommandError(f"Content JSON not found: {path}")
        try:
            modules = json.loads(path.read_text(encoding="utf-8"))["modules"]
        except Exception as exc:
            raise CommandError(f"Cannot read content JSON: {exc}")
        if len(modules) != 45:
            raise CommandError(f"Expected 45 lessons, found {len(modules)}.")
        for item in modules:
            if len(item.get("vocabulary", [])) != 5 or len(item.get("questions", [])) != 10:
                raise CommandError(f"Invalid vocabulary/question count: {item.get('title')}")
            for q in item["questions"]:
                if q.get("correct_answer") not in ("A", "B", "C", "D"):
                    raise CommandError(f"Invalid answer key in {item['title']}")
                if any(not q.get(k) for k in ("question_text","option_a","option_b","option_c","option_d","explanation")):
                    raise CommandError(f"Incomplete question in {item['title']}")
        if options["dry_run"]:
            self.stdout.write(self.style.SUCCESS("Validation passed: 45 lessons and 450 MCQs. No database changes made."))
            return

        made_lesson = changed_lesson = made_quiz = changed_quiz = 0
        with transaction.atomic():
            for item in modules:
                lesson, created = Lesson.objects.update_or_create(
                    level=item["level"], stage_number=item["stage_number"], topic_number=item["topic_number"],
                    defaults={k:item[k] for k in ("title","description","content","vocabulary","grammar_points","estimated_minutes","order")}
                    | {"is_active": True}
                )
                made_lesson += int(created)
                changed_lesson += int(not created)
                quiz, q_created = Quiz.objects.update_or_create(
                    lesson=lesson, title=item["quiz_title"],
                    defaults={"description":f"Knowledge check for {item['title']}"}
                )
                made_quiz += int(q_created)
                changed_quiz += int(not q_created)
                quiz.questions.all().delete()
                Question.objects.bulk_create([
                    Question(quiz=quiz, question_text=q["question_text"], option_a=q["option_a"],
                             option_b=q["option_b"], option_c=q["option_c"], option_d=q["option_d"],
                             correct_answer=q["correct_answer"], explanation=q["explanation"])
                    for q in item["questions"]
                ])
        self.stdout.write(self.style.SUCCESS(
            f"Import complete: {made_lesson} lessons created, {changed_lesson} updated; "
            f"{made_quiz} quizzes created, {changed_quiz} updated; 450 questions imported. "
            "Lesson progress was not deleted."
        ))
