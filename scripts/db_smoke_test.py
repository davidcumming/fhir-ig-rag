import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

def main() -> None:
    load_dotenv()
    url = os.environ["DATABASE_URL"]
    engine = create_engine(url, pool_pre_ping=True)

    with engine.connect() as conn:
        value = conn.execute(text("select 1")).scalar_one()
        version = conn.execute(text("select version()")).scalar_one()

    print(f"select 1 -> {value}")
    print(f"postgres -> {version}")

if __name__ == "__main__":
    main()