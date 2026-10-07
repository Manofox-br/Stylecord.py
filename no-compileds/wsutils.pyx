from libc.string cimport strcpy
from cpython.bytes cimport PyBytes_AsString

def encode_message(bytes msg):
    cdef char* c_msg = PyBytes_AsString(msg)
    return c_msg.decode("utf-8")

def build_frame(str data):
    cdef bytes payload = data.encode("utf-8")
    cdef int length = len(payload)
    return b"\x81" + bytes([length]) + payload