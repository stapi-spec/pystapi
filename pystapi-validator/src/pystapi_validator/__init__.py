import sys
import pytest

def main() -> None:
    sys.exit(pytest.main(['pystapi-validator/tests/validate_api.py']))

if __name__ == '__main__':
    main()