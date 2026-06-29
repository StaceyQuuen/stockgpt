import uuid
from contextvars import ContextVar


trace_id_var = ContextVar("trace_id", default=None)


def generate_trace_id():

    return str(uuid.uuid4())


def set_trace_id(trace_id: str):

    trace_id_var.set(trace_id)


def get_trace_id():

    return trace_id_var.get()