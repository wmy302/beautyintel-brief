import argparse
import os

import uvicorn

from app.db.base import init_db


def main() -> None:
    parser = argparse.ArgumentParser(prog="beautyintel-api")
    parser.add_argument("--host", default=os.getenv("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8001")))
    args = parser.parse_args()

    init_db()
    uvicorn.run("app.main:app", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
