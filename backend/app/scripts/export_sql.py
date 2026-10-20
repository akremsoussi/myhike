import pymysql


def dump_db():
    conn = pymysql.connect(
        host="127.0.0.1",
        user="refuges",
        password="refuges",
        database="refuges",
        charset="utf8mb4"
    )
    cur = conn.cursor()
    cur.execute("SHOW TABLES")
    tables = [r[0] for r in cur.fetchall()]

    # Dump schema
    with open("schema.sql", "w", encoding="utf-8") as f_schema:
        f_schema.write("SET FOREIGN_KEY_CHECKS = 0;\n\n")
        for table in tables:
            cur.execute(f"SHOW CREATE TABLE `{table}`")
            create_stmt = cur.fetchone()[1]
            f_schema.write(f"DROP TABLE IF EXISTS `{table}`;\n")
            f_schema.write(f"{create_stmt};\n\n")
        f_schema.write("SET FOREIGN_KEY_CHECKS = 1;\n")

    # Dump data
    with open("data.sql", "w", encoding="utf-8") as f_data:
        f_data.write("SET FOREIGN_KEY_CHECKS = 0;\n\n")
        for table in tables:
            cur.execute(f"SELECT * FROM `{table}`")
            rows = cur.fetchall()
            if not rows:
                continue
            cur.execute(f"DESCRIBE `{table}`")
            cols = [f"`{col[0]}`" for col in cur.fetchall()]
            cols_str = ", ".join(cols)

            f_data.write(f"-- Data for {table} ({len(rows)} rows)\n")
            # Batch inserts by 100 rows
            batch_size = 100
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                vals = []
                for row in batch:
                    formatted_row = []
                    for val in row:
                        if val is None:
                            formatted_row.append("NULL")
                        elif isinstance(val, (int, float)):
                            formatted_row.append(str(val))
                        elif isinstance(val, bytes):
                            formatted_row.append(f"0x{val.hex()}")
                        else:
                            # escape string
                            val_str = str(val).replace("\\", "\\\\").replace("'", "\\'")
                            formatted_row.append(f"'{val_str}'")
                    vals.append(f"({', '.join(formatted_row)})")
                joined = ",\n".join(vals)
                f_data.write(f"INSERT INTO `{table}` ({cols_str}) VALUES\n{joined};\n")
            f_data.write("\n")
        f_data.write("SET FOREIGN_KEY_CHECKS = 1;\n")

    print("Successfully exported schema.sql and data.sql")

if __name__ == "__main__":
    dump_db()

