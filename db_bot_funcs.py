import mysql.connector as sql


users_table_name = 'users'


def get_connection(username="root", db="lunchBot", password="root"):
    try:
        # cur_pass = getpass("input password: ")
        cur_pass = password
        cnx = sql.connect(user=username, password=cur_pass, database=db)
        return cnx
    except sql.Error as e:
        print(e)


def get_all_table_as_list(connection: sql.MySQLConnection, table_name: str):
    try:
        cur_con = connection
        cur_con.reset_session()
        cursor = cur_con.cursor()
        command_str = "select * from " + table_name
        cursor.execute(command_str)
        return cursor.fetchall()
    except sql.Error as e:
        print(e)


def get_all_users_id_as_list(connection: sql.MySQLConnection, table_name=users_table_name, role=None):
    try:
        cur_con = connection
        cur_con.reset_session()
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
    except sql.Error as e:
        print(e)


def delete(connection: sql.MySQLConnection, table_name: str, cond: str):
    try:
        cur_con = connection
        # cur_con.reset_session()
        cursor = cur_con.cursor()
        table_name = table_name.strip("'")
        cond = cond.strip("'")

        command_str = f'delete from {table_name} where {cond};'
        cursor.execute(command_str)

        connection.commit()
    except sql.Error as e:
        print(e)

