import pyodbc


def bulk_insert(
    connection,
    table_name,
    columns,
    rows,
    batch_size=5000,
):
    if not rows:
        print(f"{table_name}: no rows to insert.")
        return 0

    column_list = ", ".join(
        f"[{column}]" for column in columns
    )

    placeholders = ", ".join(
        "?" for _ in columns
    )

    sql = (
        f"INSERT INTO [{table_name}] "
        f"({column_list}) "
        f"VALUES ({placeholders})"
    )

    cursor = connection.cursor()

    cursor.fast_executemany = True

    inserted_count = 0

    try:
        for start in range(0, len(rows), batch_size):
            batch = rows[start:start + batch_size]

            values = [
                tuple(row[column] for column in columns)
                for row in batch
            ]

            cursor.executemany(
                sql,
                values,
            )

            inserted_count += len(values)

            print(
                f"{table_name}: "
                f"{inserted_count}/{len(rows)} rows inserted."
            )

        return inserted_count

    except pyodbc.Error:
        raise

    finally:
        cursor.close()