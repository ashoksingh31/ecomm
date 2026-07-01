"""
Dev-only helper to mint a JWT for manual testing, since login/auth is
explicitly out of scope for this assignment (ASSUMPTIONS.md #1).

Usage:
    python scripts/generate_test_token.py --user-id 1
    python scripts/generate_test_token.py --user-id 99 --admin
"""

import argparse
import sys
from pathlib import Path

# Allow running this script directly without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.security import create_access_token  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a test JWT for the ecom-backend API")
    parser.add_argument("--user-id", type=int, required=True, help="user_id claim to embed")
    parser.add_argument("--admin", action="store_true", help="set is_admin=True")
    args = parser.parse_args()

    token = create_access_token(user_id=args.user_id, is_admin=args.admin)
    print(token)
