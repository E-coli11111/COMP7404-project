import pandas as pd
import json

from sympy import solve, symbols, Eq, sympify
from sympy.parsing.latex import parse_latex
from abc import ABC, abstractmethod
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

class Agent(ABC):
    @abstractmethod
    def execute(self, query, limit=50):
        """
        Execute a SQL query and return the result as a DataFrame.
        """
        pass

    @abstractmethod
    def _is_safe(self, query):
        """
        Check if the query is safe to execute.
        """
        pass

class SQLAgent(Agent):
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

    def execute(self, query, limit=50):
        if not query.strip():
            raise Exception("Empty query is not allowed.")
        
        # Security
        if self.safe_mode:
            if not self._is_safe(query):
                raise Exception("Query contains unsafe operations. Only SELECT queries are allowed in safe mode.")

        try:
            result = self.connection.execute(text(query))
            
            columns = result.keys()
            rows = result.fetchmany(limit)

            df = pd.DataFrame(rows, columns=columns)

            df.insert(0, '#', range(1, len(df) + 1))
            
            return df.to_markdown(index=False)
        
        except SQLAlchemyError as e:
            return f"Error when executing: {str(e)}"
    
    def _is_safe(self, _):
        return self.safe_mode and self.db_type in ['sqlite', 'mysql', 'postgresql'] and not any(op in _ for op in ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE'])
    

class Calculator(Agent):
    def __init__(self, safe_mode=True):
        self.safe_mode = safe_mode

    def execute(self, query):
        if not query.strip():
            raise Exception("Empty query is not allowed.")
        
        args = json.loads(query) if isinstance(query, str) else query
        
        # Security
        if self.safe_mode:
            if not self._is_safe(query):
                raise Exception("Query contains unsafe operations. Only SELECT queries are allowed in safe mode.")

        try:
            variables = args['variable'].split()
            s = symbols(variables)
            equations = []
            for eq_str in args['equations']:
                if '=' in eq_str:
                    left, right = eq_str.split('=', 1)
                    equations.append(Eq(sympify(left.strip()), sympify(right.strip())))
                else:
                    equations.append(Eq(sympify(eq_str.strip()), 0))
            target_var = args['target']
            # Find the symbol corresponding to the target variable
            # Support multiple target symbols
            target_vars = target_var.split()
            target_symbols = []
            for name in target_vars:
                found = False
                for sym, var_name in zip(s, variables):
                    if var_name == name:
                        target_symbols.append(sym)
                        found = True
                        break
                if not found:
                    raise Exception(f"Target variable '{name}' not found in variables list.")
                
            if not target_symbols:
                raise Exception(f"Target variable '{target_var}' not found in variables list.")
            result = solve(equations, target_symbols)
            
            if isinstance(result, dict):
                result = {str(k): v for k, v in result.items()}
                
            return str(result)
        
        except Exception as e:
            return f"Error when executing: {str(e)}"

    def _is_safe(self, query):
        return True
    