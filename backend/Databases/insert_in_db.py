# insert_in_db.py

import asyncio
import sys
from pathlib import Path, PureWindowsPath

import pandas as pd
from sqlalchemy import text

from Database import engine
from Schema import ImagesTable


CSV_FILE_PATH = r"E:\Diploma_ISU\FinalProject\dataset\metadata_dataset.csv"


def normalize_sex(value):
    if pd.isna(value):
        return None
    value = str(value).strip().lower()
    if value in {"w", "m"}:
        return value
    return None


async def check_connection():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        print("Подключение к базе данных успешно:", result.scalar_one())


def build_records(df: pd.DataFrame):
    df = df.copy()

    # Приводим путь к единому виду
    df["storage_path"] = df["path_to_img"].astype(str).str.replace("\\", "/", regex=False)

    # Достаём имя файла из Windows-пути
    df["filename"] = df["path_to_img"].apply(lambda x: PureWindowsPath(str(x)).name)

    # patient_id должен быть строкой, потому что в БД это varchar(50)
    df["patient_id"] = df["id"].apply(lambda x: f"{int(x)}")

    # age -> целое число или None
    df["age"] = pd.to_numeric(df["age"], errors="coerce")

    # sex -> w / m
    df["sex"] = df["sex"].apply(normalize_sex)
    if df["sex"].isna().any():
        bad_rows = df.loc[df["sex"].isna(), "id"].tolist()
        raise ValueError(f"Некорректные значения sex в строках с id: {bad_rows}")

    df["metadata"] = [{} for _ in range(len(df))]

    records = []
    for row in df[["patient_id", "filename", "storage_path", "age", "sex", "metadata"]].itertuples(index=False):
        records.append(
            {
                "patient_id": row.patient_id,
                "filename": row.filename,
                "storage_path": row.storage_path,
                "age": None if pd.isna(row.age) else int(row.age),
                "sex": row.sex,
                "metadata": row.metadata,
            }
        )

    return records


async def insert_data_from_csv(csv_file_path: str):
    csv_path = Path(csv_file_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Файл не найден: {csv_path}")

    df = pd.read_csv(csv_path)
    print(f"Прочитан CSV. Строк: {len(df)}")
    print(f"Столбцы: {list(df.columns)}")

    required_columns = {"id", "age", "sex", "path_to_img"}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"В CSV отсутствуют столбцы: {sorted(missing)}")

    if df["id"].duplicated().any():
        dups = df.loc[df["id"].duplicated(keep=False), "id"].tolist()
        raise ValueError(f"Дубликаты id в CSV: {dups}")

    records = build_records(df)
    print(f"Подготовлено записей: {len(records)}")
    print("Пример записи:", records[0])

    async with engine.begin() as conn:
        await conn.execute(ImagesTable.__table__.insert(), records)

    print("Данные успешно вставлены в таблицу images.")


async def main():
    try:
        await check_connection()
        await insert_data_from_csv(CSV_FILE_PATH)
    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
