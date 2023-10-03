import psycopg2 as pg
import csv
import pandas as pd
# from yummyBot import orders_table_name, users_table_name, db_pass, db_name, db_username

try:
    with open('yummyBot.ini', 'r', encoding='utf-8') as ini_file:
        lines = ini_file.readlines()
        for line in lines:
            if line.startswith('db_name'):
                db_name = line.split('=')[-1].strip('\n')
            elif line.startswith('db_pass'):
                db_pass = line.split('=')[-1].strip('\n')
            elif line.startswith('db_username'):
                db_username = line.split('=')[-1].strip('\n')
            elif line.startswith('users_table_name'):
                users_table_name = line.split('=')[-1].strip('\n')
            elif line.startswith('orders_table_name'):
                orders_table_name = line.split('=')[-1].strip('\n')
        ini_file.close()

except Exception as e:
    print(e)


def get_connection(username=db_username, db=db_name, password=db_pass):
    try:
        # cur_pass = getpass("input password: ")
        cur_pass = password
        cnx = pg.connect(user=username, password=cur_pass, database=db)
        return cnx
    except pg.Error as e:
        print(e)


def get_all_table_as_list(connection: pg.extensions.connection, table_name: str):
    try:
        cur_con = connection
        # cur_con.reset_session()
        cursor = cur_con.cursor()
        command_str = "select * from " + table_name
        cursor.execute(command_str)
        return cursor.fetchall()
    except pg.Error as e:
        print(e)


def get_all_users_id_as_list(connection: pg.extensions.connection,
                             table_name=users_table_name, role=None):
    try:
        cur_con = connection
        # cur_con.reset_session()
        cursor = cur_con.cursor()
        command_str = f'select user_tgid from {table_name}'
        if role is not None:
            command_str += f" where {table_name}.special_role='{role}';"
        else:
            command_str += ';'
        cursor.execute(command_str)
        arr = cursor.fetchall()
        result = []
        for tup in arr:
            result.append(tup[0])
        return result
    except pg.Error as e:
        print(e)


def get_all_users_nicknames_as_dict(connection: pg.extensions.connection, table_name=users_table_name):
    try:
        cur_con = connection
        # cur_con.reset_session()
        cursor = cur_con.cursor()
        command_str = f'select user_tgid, first_name, last_name from {table_name};'
        cursor.execute(command_str)
        arr = cursor.fetchall()
        result = {}

        for tup in arr:
            result.update({tup[0]: f'{tup[1]} {tup[2]}'})
        return result
    except pg.Error as e:
        print(e)


def get_table_columns(connection: pg.extensions.connection, table_name):
    try:
        cur_con = connection
        # cur_con.reset_session()
        cursor = cur_con.cursor()
        command_str = f'select * from {table_name} limit 0;'
        cursor.execute(command_str)
        colnames = [desc[0] for desc in cursor.description]
        return colnames
    except pg.Error as e:
        print(e)


def update(connection: pg.extensions.connection, table_name: str, index: str, res: str, cond: str):
    try:
        table_name = table_name.strip("'")
        index = index.strip("'")
        res = res.strip("'")
        command_str = f"""update {table_name} set {index} = "{res}" where {cond}"""
        cur_con = connection
        # cur_con.reset_session()
        cursor = cur_con.cursor(prepared=True)
        cursor.execute(command_str)
        connection.commit()
    except pg.Error as e:
        print(e)


def insert(connection: pg.extensions.connection, table_name: str, params: str, value: str):
    try:
        cur_con = connection
        # cur_con.reset_session()
        cursor = cur_con.cursor()
        insert_query = f""" insert into {table_name} {params} values {value}"""
        cursor.execute(insert_query)

        # for i in values:
        #     i = i.strip("'")
        #     command_str = f"""insert into {table_name} {params} values {tuple(i)};"""
        #     cursor.execute(command_str)
        connection.commit()
    except pg.Error as e:
        print(e)


def delete(connection: pg.extensions.connection, table_name: str, cond: str):
    try:
        cur_con = connection
        # cur_con.reset_session()
        cursor = cur_con.cursor()
        table_name = table_name.strip("'")
        cond = cond.strip("'")

        command_str = f'delete from {table_name} where {cond};'
        cursor.execute(command_str)

        connection.commit()
    except pg.Error as e:
        print(e)


def get_all_table_as_dataframe(connection: pg.extensions.connection, table_name: str, reset=True):
    try:
        cur_con = connection
        if reset:
            cur_con.reset_session()
        cursor = cur_con.cursor(prepared=True)
        command_str = "select * from " + table_name
        cursor.execute(command_str)
        res = pd.DataFrame(cursor.fetchall())
        res.columns = cursor.column_names
        # command_str = f"SHOW KEYS FROM {table_name} WHERE Key_name = 'PRIMARY'"
        # cursor.execute(command_str)
        # keys = cursor.fetchall()
        # res.set_index(keys[0][4], inplace=True)
        cursor.close()
        return res
    except pg.Error as e:
        print(e)


def export_table_as_csv(connection: pg.extensions.connection, table_name: str, file_name: str):
    try:
        cur_con = connection
        cur_con.reset_session()

        cursor = cur_con.cursor()
        cursor.execute(f'Select * from {table_name};')
        data = cursor.fetchall()

        with open(f'{file_name}', 'w') as f:
            writer = csv.writer(f)
            writer.writerow([x[0] for x in cursor.description])
            for row in data:
                writer.writerow(row)

        cursor.close()

    except pg.Error as e:
        print(e)


def export_users_orders(connection: pg.extensions.connection,
                        table_name: str, file_name: str, user_tgid):
    try:
        cur_con = connection
        cur_con.reset_session()

        cursor = cur_con.cursor()
        cursor.execute(f'Select * from {table_name} where user_tgid = {user_tgid};')
        data = cursor.fetchall()

        with open(f'{file_name}', 'w') as f:
            writer = csv.writer(f)
            writer.writerow([x[0] for x in cursor.description])
            for row in data:
                writer.writerow(row)

        cursor.close()

    except pg.Error as e:
        print(e)


def user_total(connection: pg.extensions.connection, table_name: str, user_tgid):
    try:
        command_str = f'select total_in_month from {table_name} where user_tgid={user_tgid};'
        cursor = connection.cursor()
        cursor.execute(command_str)

        result = cursor.fetchall()

        return result[0][0]

    except Exception as e:
        print(e)


def increase_func(connection: pg.extensions.connection, table_name: str,
                  index: str, res: str, cond: str):
    try:
        table_name = table_name.strip("'")
        index = index.strip("'")
        res = res.strip("'")
        command_str = f"""update {table_name} set {index} = {res} where {cond}"""
        cur_con = connection
        # cur_con.reset_session()
        cursor = cur_con.cursor(prepared=True)
        cursor.execute(command_str)
        connection.commit()
    except pg.Error as e:
        print(e)


if __name__ == '__main__':
    con = get_connection()
    print(get_all_users_nicknames_as_dict(con))
