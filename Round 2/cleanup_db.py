"""
Cleanup script for ML Fest Round 2.
Truncates all participant data from mlfest_db (PostgreSQL).
Keeps the admin superuser and challenge/event config intact.

Usage:
    python cleanup_db.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mlfest.settings')
django.setup()

from django.db import connection


def cleanup():
    db_name = connection.settings_dict['NAME']
    print("=" * 60)
    print(f"  ML Fest Round 2 -- Cleanup [{db_name}]")
    print("=" * 60)
    print()

    with connection.cursor() as cursor:
        cursor.execute('TRUNCATE TABLE "debugchallenge_evaluation" CASCADE;')
        print("[OK] Truncated debugchallenge_evaluation")

        cursor.execute('TRUNCATE TABLE "debugchallenge_submission" CASCADE;')
        print("[OK] Truncated debugchallenge_submission")

        cursor.execute('TRUNCATE TABLE "debugchallenge_participant" CASCADE;')
        print("[OK] Truncated debugchallenge_participant")

        cursor.execute('TRUNCATE TABLE "debugchallenge_challenge" CASCADE;')
        print("[OK] Truncated debugchallenge_challenge")

        cursor.execute('TRUNCATE TABLE "debugchallenge_event" CASCADE;')
        print("[OK] Truncated debugchallenge_event")

        cursor.execute('DELETE FROM "auth_user" WHERE is_staff = FALSE;')
        deleted = cursor.rowcount
        print(f"[OK] Deleted {deleted} non-admin user(s) from auth_user")

        cursor.execute('TRUNCATE TABLE "django_session" CASCADE;')
        print("[OK] Truncated django_session")

    print()
    print("=" * 60)
    print(f"  Cleanup complete! Database [{db_name}] cleared.")
    print("  Admin superuser preserved.")
    print("=" * 60)


if __name__ == '__main__':
    db_name = os.environ.get('DB_NAME', 'mlfest_db')
    confirm = input(
        f"This will TRUNCATE all participant data in [{db_name}].\n"
        "Admin superuser will be preserved. Continue? (yes/no): "
    )
    if confirm.lower() != 'yes':
        print("Aborted.")
    else:
        cleanup()
