#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py seed_complete_curriculum
python manage.py seed_practicehub
python load_assessment_questions.py
python seed_vnotes.py
python manage.py seed_interview_questions
