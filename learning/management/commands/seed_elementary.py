import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from learning.models import Lesson, Quiz, Question


def canonical_title(value):
    """Normalize known title spelling/punctuation differences in old seed data."""
    value = "".join(ch.lower() if ch.isalnum() else " " for ch in value)
    value = " ".join(value.split())
    aliases = {
        "comparisions": "comparisons",
        "suggestions and advive": "suggestions advice",
    }
    return aliases.get(value, value)


class Command(BaseCommand):
    help = "Import the 15 Elementary lessons and their source-document practice tests."

    @transaction.atomic
    def handle(self, *args, **options):
        data_path = Path(settings.BASE_DIR) / "learning" / "data" / "elementary_lessons.json"
        if not data_path.exists():
            raise CommandError(
                f"Elementary data file not found: {data_path}. "
                "Place elementary_lessons.json in learning/data/ first."
            )

        with data_path.open("r", encoding="utf-8") as file:
            lesson_data = json.load(file)

        if len(lesson_data) != 15:
            raise CommandError(
                f"Expected 15 Elementary lessons in the data file; found {len(lesson_data)}."
            )

        existing_lessons = list(Lesson.objects.filter(level="ELEMENTARY"))
        by_title = {}
        for lesson in existing_lessons:
            key = canonical_title(lesson.title)
            if key in by_title:
                raise CommandError(
                    f"Duplicate existing Elementary lesson title detected: {lesson.title}. "
                    "Resolve duplicates in Django Admin before importing."
                )
            by_title[key] = lesson

        # First move/update title-matched existing lessons. This preserves their
        # LessonProgress and QuizAttempt relationships while correcting old stage data.
        matched_ids = set()
        for item in lesson_data:
            old_lesson = by_title.get(canonical_title(item["title"]))
            if old_lesson:
                self.update_lesson(old_lesson, item)
                matched_ids.add(old_lesson.pk)

        created_lessons = 0
        updated_lessons = len(matched_ids)
        lesson_objects = []

        # Add the remaining lessons, reusing an unused stage/topic slot if present.
        for item in lesson_data:
            lesson = by_title.get(canonical_title(item["title"]))
            if lesson is None:
                lesson = Lesson.objects.filter(
                    level="ELEMENTARY",
                    stage_number=item["stage_number"],
                    topic_number=item["topic_number"],
                ).exclude(pk__in=matched_ids).first()
                if lesson:
                    self.update_lesson(lesson, item)
                    matched_ids.add(lesson.pk)
                    updated_lessons += 1
                else:
                    lesson = Lesson.objects.create(
                        level="ELEMENTARY",
                        stage_number=item["stage_number"],
                        topic_number=item["topic_number"],
                        title=item["title"],
                        description=item["description"],
                        content=item["content"],
                        vocabulary=item["vocabulary"],
                        grammar_points=[],
                        estimated_minutes=item.get("estimated_minutes", 15),
                        order=item.get("order", item["topic_number"]),
                        is_active=True,
                    )
                    created_lessons += 1
            lesson_objects.append((lesson, item))

        created_quizzes = 0
        created_questions = 0
        updated_questions = 0

        for lesson, item in lesson_objects:
            quizzes = Quiz.objects.filter(lesson=lesson)
            if quizzes.count() > 1:
                raise CommandError(
                    f"More than one quiz exists for '{lesson.title}'. "
                    "Resolve this in Django Admin before importing."
                )

            quiz = quizzes.first()
            if quiz is None:
                quiz = Quiz.objects.create(
                    lesson=lesson,
                    title=f"{lesson.title} - Practice Test",
                    description=f"Practice test for Stage {item['stage_number']}, Level {item['topic_number']}: {lesson.title}.",
                )
                created_quizzes += 1
            else:
                quiz.title = f"{lesson.title} - Practice Test"
                quiz.description = (
                    f"Practice test for Stage {item['stage_number']}, "
                    f"Level {item['topic_number']}: {lesson.title}."
                )
                quiz.save(update_fields=["title", "description"])

            for question_data in item["quiz_questions"]:
                answer = question_data["correct_answer"]
                if answer not in ("A", "B", "C", "D"):
                    raise CommandError(
                        f"Invalid answer key for '{lesson.title}': {answer!r}"
                    )

                _, was_created = Question.objects.update_or_create(
                    quiz=quiz,
                    question_text=question_data["question_text"],
                    defaults={
                        "option_a": question_data["option_a"],
                        "option_b": question_data["option_b"],
                        "option_c": question_data["option_c"],
                        "option_d": question_data["option_d"],
                        "correct_answer": answer,
                        "explanation": question_data.get("explanation", ""),
                    },
                )
                if was_created:
                    created_questions += 1
                else:
                    updated_questions += 1

        self.stdout.write(self.style.SUCCESS("Elementary module import completed."))
        self.stdout.write(f"Lessons created: {created_lessons}")
        self.stdout.write(f"Existing lessons updated: {updated_lessons}")
        self.stdout.write(f"Practice tests created: {created_quizzes}")
        self.stdout.write(f"Questions created: {created_questions}")
        self.stdout.write(f"Existing questions updated: {updated_questions}")
        self.stdout.write(
            "Source note: 149 MCQs have answer keys. The source document's "
            "Stage 6, Level 2, Question 10 has no answer key, so it was not imported."
        )

    @staticmethod
    def update_lesson(lesson, item):
        lesson.level = "ELEMENTARY"
        lesson.stage_number = item["stage_number"]
        lesson.topic_number = item["topic_number"]
        lesson.title = item["title"]
        lesson.description = item["description"]
        lesson.content = item["content"]
        lesson.vocabulary = item["vocabulary"]
        lesson.grammar_points = []
        lesson.estimated_minutes = item.get("estimated_minutes", 15)
        lesson.order = item.get("order", item["topic_number"])
        lesson.is_active = True
        lesson.save()
