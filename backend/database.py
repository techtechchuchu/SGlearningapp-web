"""Request-scoped, parameterized Postgres adapter for the legacy table API.
Every mutating request is one transaction; no production connection at import.
"""
import re
from contextvars import ContextVar
from types import SimpleNamespace
connection = ContextVar('database_connection', default=None)
TABLES={'users','wrong_answers','student_roster','print_status','school_exam_master','school_exam_wrong_answers','book_master','password_reset_requests','notices','school_exam_grade_imports'}
def ident(s):
    if not re.fullmatch(r'[a-z_][a-z_0-9]*',s): raise ValueError('Invalid SQL identifier')
    return '"'+s+'"'
class Query:
    def __init__(self,table):
        if table not in TABLES: raise ValueError('Unknown table')
        self.table=table;self.columns='*';self.filters=[];self.values=[];self.mode='select';self.payload=None;self.sort='';self.take=None;self.offset=0;self.conflict=None
    def select(self,columns='*',count=None):
        self.columns='*' if columns=='*' else ','.join(ident(x.strip()) for x in columns.split(','));return self
    def eq(self,col,val): self.filters.append(ident(col)+' = %s');self.values.append(val);return self
    def neq(self,col,val): self.filters.append(ident(col)+' <> %s');self.values.append(val);return self
    def in_(self,col,values):
        self.filters.append(ident(col)+' IN ('+','.join(['%s']*len(values))+')' if values else 'FALSE');self.values.extend(values);return self
    def order(self,col,desc=False): self.sort=' ORDER BY '+ident(col)+(' DESC' if desc else ' ASC');return self
    def limit(self,n):self.take=int(n);return self
    def range(self,start,end):self.offset=int(start);self.take=int(end)-int(start)+1;return self
    def insert(self,payload):self.mode='insert';self.payload=payload;return self
    def upsert(self,payload,on_conflict=None):self.mode='insert';self.payload=payload;self.conflict=on_conflict;return self
    def update(self,payload):self.mode='update';self.payload=payload;return self
    def delete(self):self.mode='delete';return self
    def execute(self):
        conn=connection.get()
        if conn is None:raise RuntimeError('Database request context missing')
        where=' WHERE '+' AND '.join(self.filters) if self.filters else ''
        table=ident(self.table);values=list(self.values)
        if self.mode=='select':
            query='SELECT '+self.columns+' FROM '+table+where+self.sort
            if self.take is not None:query+=' LIMIT %s OFFSET %s';values.extend([self.take,self.offset])
        elif self.mode=='delete':
            if not self.filters:raise ValueError('Unfiltered delete forbidden')
            query='DELETE FROM '+table+where+' RETURNING *'
        elif self.mode=='update':
            if not self.filters:raise ValueError('Unfiltered update forbidden')
            query='UPDATE '+table+' SET '+','.join(ident(k)+' = %s' for k in self.payload)+where+' RETURNING *';values=list(self.payload.values())+values
        else:
            rows=self.payload if isinstance(self.payload,list) else [self.payload]
            if not rows:return SimpleNamespace(data=[],count=0)
            keys=list(rows[0]);values=[]
            if any(set(row)!=set(keys) for row in rows):raise ValueError('Mixed insert columns')
            query='INSERT INTO '+table+' ('+','.join(map(ident,keys))+') VALUES '+','.join('('+','.join(['%s']*len(keys))+')' for _ in rows)
            for row in rows:values.extend(row[k] for k in keys)
            if self.conflict:
                cols=[c.strip() for c in self.conflict.split(',')]
                query+=' ON CONFLICT ('+','.join(map(ident,cols))+') DO UPDATE SET '+','.join(ident(k)+' = EXCLUDED.'+ident(k) for k in keys if k not in cols)
            query+=' RETURNING *'
        with conn.cursor() as cur:
            cur.execute(query,values);rows=cur.fetchall()
        return SimpleNamespace(data=rows,count=len(rows))
class Database:
    def table(self,name):return Query(name)
database=Database()
