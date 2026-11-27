# Render deployment checklist

## Build command

```bash
./build.sh
```

## Start command

```bash
gunicorn fluent_ai.wsgi:application
```

## Required environment variables

- `DJANGO_SECRET_KEY`: generate a new long random secret. Do not reuse the old hardcoded key.
- `DEBUG`: `False`
- `ALLOWED_HOSTS`: `fluent-ai-2yz8.onrender.com`
- `CSRF_TRUSTED_ORIGINS`: `https://fluent-ai-2yz8.onrender.com`
- `DATABASE_URL`: Render PostgreSQL Internal Database URL (recommended for persistent user data).
- `OPENAI_API_KEY`: API key from the AI provider.
- `OPENAI_MODEL`: `gpt-4o-mini` unless a different model is enabled for the key.

`DATABASE_URL` may be omitted for local development, where SQLite is used. Do not rely on SQLite on an ephemeral Render filesystem for production data.

## After deployment

1. Confirm the latest deploy completed successfully.
2. Check `/` and `/admin/`.
3. Create an admin user with `python manage.py createsuperuser` using the Render Shell.
4. Test registration, login, MCQ assessment, writing assessment, and AI Tutor.
5. Confirm the PostgreSQL database is attached and migrations completed.

Never commit `.env`, API keys, database URLs, or real credentials.
