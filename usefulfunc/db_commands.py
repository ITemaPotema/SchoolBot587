import sqlite3 as sq


def insert_db(file_table_name: str, table_name: str, values: tuple, condition="", columns=""):
    with sq.connect(f"{file_table_name}") as con:
        cur = con.cursor()
        text = f"""
        INSERT INTO {table_name} {columns}
        VALUES({'?, ' * (len(values)-1) + '?'}) {condition}
        """
        cur.execute(text, values)


def select(file_table_name, table_name, values, condition=""):
    with sq.connect(f"{file_table_name}") as con:
        cur = con.cursor()
        text = f"""
        SELECT {", ".join(values) if values != "*" else "*"}
        FROM {table_name}
        {condition}
        """
        cur.execute(text)
        return cur.fetchall()


def update_db(file_table_name, table_name, col, value, condition=""):
    with sq.connect(f"{file_table_name}") as con:
        cur = con.cursor()
        text = f"""
        UPDATE {table_name} SET {col} = '{value}'
        {condition}
        """
        cur.execute(text)

