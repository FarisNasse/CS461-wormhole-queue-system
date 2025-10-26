# Credit to ArjanCodes on GitHub for the original code structure.
# Youtube Guide: https://www.youtube.com/watch?v=aAy-B6KPld8&t=535s
# Repository: https://github.com/ArjanCodes/examples/blob/main/2024/sqlalchemy/simple_approach.py

import sqlalchemy as sa

engine = sa.create_engine("sqlite:///:memory:", echo=True)
connection = engine.connect()

metadata = sa.MetaData()

# Define the tickets table
tickets_table = sa.Table(
    "tickets",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("student_name", sa.String),
    sa.Column("table_number", sa.Integer),
    sa.Column("class_name", sa.String),
    sa.Column("status", sa.String),
    sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    sa.Column("deactivated_at", sa.DateTime, nullable=True),
    sa.Column("num_students", sa.Integer, nullable=True),
    sa.Column("current_wa", sa.String, nullable=True)
)

# Simulate a wormhole button box being pressed. The button numbers are mapped to class names.
def button(button_pressed: int) -> None:
    match button_pressed:
        case 1:
            class_name = "Physics 211"
        case 2:
            class_name = "Physics 212"
        case 3:
            class_name = "Physics 213"
        case 4:
            class_name = "Physics 201"
        case _:
            raise ValueError("Invalid button pressed")
    query = tickets_table.insert().values(student_name="student", table_number=1, class_name=class_name, status="waiting")
    connection.execute(query)

# Select tickets by class name
def select_class(class_name: str) -> sa.engine.Result:
    query = tickets_table.select().where(tickets_table.c.class_name == class_name)
    result = connection.execute(query)
    return result.fetchone()


def main() -> None:
    metadata.create_all(engine)
    button(1)
    button(2)
    button(3)
    print(select_class("Physics 211"))
    connection.close()


if __name__ == "__main__":
    main()