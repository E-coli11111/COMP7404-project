import pandas as pd

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

class SQLAgent:
    def __init__(self, db_type='sqlite', db_name=None, username=None, password=None, host=None, port=None):
        """
        Initialize the SQLAgent with database connection parameters.
        """
        self.db_type = db_type.lower()
        self.db_name = db_name.lower()
        self.connection = None
        self.engine = None
        self.safe_mode = True  
        
        if self.db_type == 'sqlite':
            if not db_name:
                db_name = ':memory:'
            self.engine = create_engine(f'sqlite:///{db_name}')
            self.connection = self.engine.connect()
            
        elif self.db_type == 'mysql':
            if not all([db_name, username, password, host]):
                raise ValueError("Missing parameters for MySQL: db_name, username, password, host")
            conn_str = f"mysql+pymysql://{username}:{password}@{host}:{port or 3306}/{db_name}"
            self.engine = create_engine(conn_str)
            self.connection = self.engine.connect()
            
        elif self.db_type == 'postgresql':
            if not all([db_name, username, password, host]):
                raise ValueError("Missing parameters for PostgreSQL: db_name, username, password, host")
            conn_str = f"postgresql://{username}:{password}@{host}:{port or 5432}/{db_name}"
            self.engine = create_engine(conn_str)
            self.connection = self.engine.connect()
            
        else:
            raise ValueError(f"Database {db_type} is not supported. Currently supported database: sqlite, mysql, postgresql")

    def execute_query(self, query, limit=50):
        if not query.strip():
            raise Exception("Empty query is not allowed.")
        
        # Security
        if self.safe_mode:
            if not self._is_safe_query(query):
                raise Exception("Query contains unsafe operations. Only SELECT queries are allowed in safe mode.")

        try:
            result = self.connection.execute(text(query))
            
            columns = result.keys()
            rows = result.fetchmany(limit)

            df = pd.DataFrame(rows, columns=columns)

            df.insert(0, '#', range(1, len(df) + 1))
            
            return df
        
        except SQLAlchemyError as e:
            return f"Error when executing: {str(e)}"
    
    def _is_safe_query(self, query):
        return True
    
if __name__ == "__main__":
    # Example usage
    agent = SQLAgent(db_type='mysql', host='localhost', username='root', password='test', db_name='test')

    query = "SHOW tables;"
    result = agent.execute_query(query)
    
    print(result)