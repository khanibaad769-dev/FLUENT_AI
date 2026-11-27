import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from learning.models import Lesson, Quiz, Question


class Command(BaseCommand):
    help = "Import the complete 60-lesson Fluent AI curriculum."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            default="data/FLUENT_AI_complete_curriculum_60_lessons.json",
            help="Path to the consolidated curriculum JSON, relative to BASE_DIR.",
        )
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        path = Path(options["file"])
        if not path.is_absolute():
            from django.conf import settings
            path = settings.BASE_DIR / path

        if not path.exists():
            raise CommandError(
                f"Curriculum file not found: {path}\n"
                "Place FLUENT_AI_complete_curriculum_60_lessons.json in the project's data/ folder."
            )

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            modules = data["modules"]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise CommandError(f"Cannot read curriculum JSON: {exc}")

        if len(modules) != 60:
            raise CommandError(f"Expected 60 lessons; found {len(modules)}.")

        expected_levels = {"BEGINNER", "ELEMENTARY", "INTERMEDIATE", "ADVANCED"}
        counts = {level: sum(m.get("level") == level for m in modules) for level in expected_levels}
        if counts != {level: 15 for level in expected_levels}:
            raise CommandError(f"Expected 15 lessons per level; found {counts}.")

        seen_slots = set()
        for item in modules:
            slot = (item.get("level"), item.get("stage_number"), item.get("topic_number"))
            if slot in seen_slots:
                raise CommandError(f"Duplicate lesson slot: {slot}")
            seen_slots.add(slot)

            required = ("title", "description", "content", "quiz_title")
            if any(not item.get(key) for key in required):
                raise CommandError(f"Missing lesson/quiz information in: {item.get('title', 'unknown lesson')}")

            questions = item.get("questions", [])
            if len(questions) != 10:
                raise CommandError(f"{item['title']}: expected 10 questions, found {len(questions)}.")

            for number, question in enumerate(questions, start=1):
                required_question_fields = (
                    "question_text", "option_a", "option_b", "option_c",
                    "option_d", "correct_answer", "explanation"
                )
                if any(not question.get(key) for key in required_question_fields):
                    raise CommandError(f"{item['title']}, question {number}: missing required field.")
                if question["correct_answer"] not in {"A", "B", "C", "D"}:
                    raise CommandError(f"{item['title']}, question {number}: invalid answer key.")

        if options["dry_run"]:
            self.stdout.write(self.style.SUCCESS(
                "Validation passed: 60 lessons, 4 levels, 600 MCQs. No database changes made."
            ))
            return

        created_lessons = updated_lessons = created_quizzes = updated_quizzes = 0
        imported_questions = 0

        with transaction.atomic():
            for item in modules:
                lesson, created = Lesson.objects.update_or_create(
                    level=item["level"],
                    stage_number=item["stage_number"],
                    topic_number=item["topic_number"],
                    defaults={
                        "title": item["title"],
                        "description": item["description"],
                        "content": item["content"],
                        "vocabulary": item.get("vocabulary", []),
                        "grammar_points": item.get("grammar_points", []),
                        "estimated_minutes": item.get("estimated_minutes", 15),
                        "order": item.get("order", item["topic_number"]),
                        "is_active": True,
                    },
                )
                created_lessons += int(created)
                updated_lessons += int(not created)

                # Reuse an existing quiz for this lesson where possible. This avoids
                # creating a duplicate quiz and preserves references to quiz attempts.
                quiz = Quiz.objects.filter(lesson=lesson, title=item["quiz_title"]).first()
                if quiz is None:
                    quiz = Quiz.objects.filter(lesson=lesson).order_by("id").first()

                if quiz is None:
                    quiz = Quiz.objects.create(
                        lesson=lesson,
                        title=item["quiz_title"],
                        description=f"10-question test for {item['title']}.",
                    )
                    created_quizzes += 1
                else:
                    quiz.title = item["quiz_title"]
                    quiz.description = f"10-question test for {item['title']}."
                    quiz.save(update_fields=["title", "description"])
                    updated_quizzes += 1

                # Replace this quiz's question bank with the verified JSON set.
                quiz.questions.all().delete()
                Question.objects.bulk_create([
                    Question(
                        quiz=quiz,
                        question_text=q["question_text"],
                        option_a=q["option_a"],
                        option_b=q["option_b"],
                        option_c=q["option_c"],
                        option_d=q["option_d"],
                        correct_answer=q["correct_answer"],
                        explanation=q.get("explanation", ""),
                    )
                    for q in item["questions"]
                ])
                imported_questions += len(item["questions"])

        self.stdout.write(self.style.SUCCESS("Complete curriculum import successful."))
        self.stdout.write(f"Lessons created: {created_lessons}")
        self.stdout.write(f"Lessons updated: {updated_lessons}")
        self.stdout.write(f"Quizzes created: {created_quizzes}")
        self.stdout.write(f"Quizzes updated/reused: {updated_quizzes}")
        self.stdout.write(f"Questions imported: {imported_questions}")
        self.stdout.write("Existing LessonProgress records were not deleted.")
