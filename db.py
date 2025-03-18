import psycopg

class DataBase:
    DATABASE_URL = "postgresql://postgres:decker12@localhost/congruentchess"
    FIELDS = ()

    def get_db_connection(self):
        return psycopg.connect(self.DATABASE_URL)

    def execute(self, string):
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute(string)
        conn.commit()
        cur.close()
        conn.close()

    def format_item(self, item, fields):
        zipped = zip(fields, item)
        return { key: value for key, value in zipped }
    
    def get(self, query, fields, all=False):
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute(query)

        if all:
            result = cur.fetchall()
        else:
            result = cur.fetchone()

        cur.close()
        conn.close()

        if all:
            return [self.format_item(i, fields) for i in result]
        else:
            return self.format_item(result, fields)


    def get_all(self, query, fields):
        return self.get(query, fields, all=True)
    
    def get_one(self, query, fields):
        return self.get(query, fields)

    def run_sql_file(self, path):
        conn = self.get_db_connection()
        cur = conn.cursor()

        with open(path, "r") as schemafile:
            sql_script = schemafile.read()

        cur.execute(sql_script)
        conn.commit()
        cur.close()
        conn.close()

    #! INIT FUNCS


    def init_db(self):
        self.run_sql_file("schema.sql")

    def reset_db(self):
        self.run_sql_file("reset.sql")

    def inject_dummy_data(self):
        self.run_sql_file("dummydata.sql")

class Model:

    DB = DataBase()

    @classmethod
    def all(cls):
        return cls.DB.get_all(f"""
            SELECT * FROM {cls.TABLE_NAME};
        """, cls.FIELDS)
    
    @classmethod
    def filter(cls, query):
        return cls.DB.get_all(query, cls.FIELDS)
    
    @classmethod
    def get_by_id(cls, game_id):
        return cls.DB.get_one(f"""
            SELECT * FROM {cls.TABLE_NAME}
            WHERE game_id='{game_id}';
        """, cls.FIELDS) 
    
    @classmethod
    def add(cls, row: tuple):

        if len(row) != len(cls.INSERT_VALUES):
            raise Exception("Incorrect number of insert values.")

        return cls.DB.execute(f"""
            INSERT INTO {cls.TABLE_NAME} {cls.INSERT_VALUES}
            VALUES {row};
        """)
    
if __name__ == "__main__":
    db = DataBase()
    # db.reset_db()
    # db.init_db()
    db.inject_dummy_data()