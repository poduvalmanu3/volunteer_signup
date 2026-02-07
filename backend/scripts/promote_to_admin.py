"""
Script to promote a user to ADMIN role for testing RBAC.

Usage:
    python -m scripts.promote_to_admin <user_email>
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.models.user import User


def promote_user_to_admin(email: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()

        if not user:
            print(f"Error: User with email '{email}' not found")
            return False

        if user.role == "ADMIN":
            print(f"User '{user.name}' ({email}) is already an ADMIN")
            return True

        user.role = "ADMIN"
        db.commit()

        print(f"Successfully promoted '{user.name}' ({email}) to ADMIN role")
        return True

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.promote_to_admin <user_email>")
        sys.exit(1)

    email = sys.argv[1]
    success = promote_user_to_admin(email)
    sys.exit(0 if success else 1)
