import sys
import pytest

def main():
    sys.exit(pytest.main(['stapi-validator/tests/validate_api.py']))

if __name__ == '__main__':
    main()