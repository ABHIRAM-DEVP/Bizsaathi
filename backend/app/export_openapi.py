"""Export OpenAPI contract as formatted JSON to stdout."""

import json
import sys

from app.main import app


def main() -> None:
    openapi_schema = app.openapi()
    output = json.dumps(openapi_schema, indent=2, ensure_ascii=False)
    sys.stdout.write(output + "\n")


if __name__ == "__main__":
    main()
