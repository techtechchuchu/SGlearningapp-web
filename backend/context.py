from contextvars import ContextVar
from types import SimpleNamespace
_state = ContextVar('request_state', default=None)
class State:
    def __getattr__(self,key): return (_state.get() or {}).get(key)
    def __getitem__(self,key): return (_state.get() or {}).get(key)
    def __setitem__(self,key,value):
        current = dict(_state.get() or {}); current[key]=value; _state.set(current)
st = SimpleNamespace(session_state=State())
