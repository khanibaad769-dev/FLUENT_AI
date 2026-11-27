#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py seed_complete_curriculum
cat >> build.sh <<'EOF'
python manage.py seed_practicehub
python load_assessment_questions.py
python seed_vnotes.py
EOF