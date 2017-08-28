#!/usr/bin/python
#author: jobs
#email: yao050421103@gmail.com
import sys
import os
import os.path
import datetime
import string
import json
import binascii
import struct
import ctypes
import mmap

sizeof_bool = 1
sizeof_int8 = 1
sizeof_uint8 = 1
sizeof_int16 = 2
sizeof_uint16 = 2
sizeof_int32 = 4
sizeof_uint32 = 4
sizeof_int64 = 8
sizeof_uint64 = 8
sizeof_float = 4
sizeof_double = 8

bool_fmt   = "<b"
int8_fmt   = "<b"
uint8_fmt  = "<B"
int16_fmt  = "<h"
uint16_fmt = "<H"
int32_fmt  = "<i"
uint32_fmt = "<I"
int64_fmt  = "<q"
uint64_fmt = "<Q"
float_fmt  = "<f"
double_fmt = "<d"

sizeof_rb_size = sizeof_uint32
sizeof_rb_field_size = sizeof_uint8
sizeof_rb_field_id = sizeof_rb_field_size
sizeof_rb_offset = sizeof_rb_size
sizeof_rb_buf_end = sizeof_uint32

rb_size_fmt = uint32_fmt
rb_field_size_fmt = uint8_fmt
rb_field_id_fmt = rb_field_size_fmt
rb_offset_fmt = rb_size_fmt
rb_buf_end_fmt = uint32_fmt

rb_field_table_head_size = sizeof_rb_size + sizeof_rb_field_size
rb_field_table_item_size = sizeof_rb_field_id + sizeof_rb_offset

def rb_seek_field_table_item(index):
    return rb_field_table_head_size + index * rb_field_table_item_size

def from_memory(fmt, buf, offset):
    return struct.unpack_from(fmt, buf, offset)[0]
def to_memory(fmt, buf, offset, data):
    struct.pack_into(fmt, buf, offset, data)

def rb_create_buf(size):
    return {
        "size": size,
        "data": bytearray(size),
        "start": 0,
        "pos": 0,
        "end": size
        }
def rb_make_buf(data, size):
    return {
        'size': size,
        'data': data,
        'start': 0,
        'pos': 0,
        'end': size
        }
def rb_nested_buf(buf, offset):
    nested_buf = rb_create_buf(0)
    if rb_check_buf(buf):
        nested_buf['data'] = buf['data']
        nested_buf['start'] = buf['pos'] if (0 == offset) else (buf['start'] + offset)
        nested_buf['end'] = buf['end']
        nested_buf['pos'] = nested_buf['start']
        nested_buf['size'] = nested_buf['end'] - nested_buf['start']
    return nested_buf
def rb_crc32(buf, fields):
    offset = rb_seek_field_table_item(fields)
    tmpbuf = buffer(buf['data'], buf['start'], offset)
    return ctypes.c_uint32(binascii.crc32(tmpbuf)).value
def rb_dump_buf(encode, obj_val, size, path):
    with open(path, 'wb') as f:
        f.seek(f.tell() + size - 1)
        f.write('\0')
    f = open(path, 'rb+')
    mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_WRITE)
    buf = rb_make_buf(mm, size)
    rc = encode(obj_val, buf)
    mm.close()
    f.close()
    return rc
def rb_load_buf(path, decode):
    file_size = os.stat(path).st_size
    f = open(path, 'rb')
    mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    size = from_memory(rb_size_fmt, mm, 0)
    obj_val = None
    rc = False
    if not (size < 1 or size > file_size):
        buf = rb_make_buf(mm, size)
        (obj_val, rc) = decode(buf, 0)
    mm.close()
    f.close()
    return (obj_val, rc)
def rb_check_buf(buf):
    return (buf['size'] > 0) and (
        buf['start'] <= buf['pos'] <= buf['end']) and (
        buf['start'] + buf['size'] <= buf['end'])
def rb_encode_check(buf, size):
    return rb_check_buf(buf) and (buf['pos'] + size < buf['end'])
def rb_decode_check(buf, offset, size):
    return rb_check_buf(buf) and (
        buf['start'] + offset + size < buf['end']) and (
        offset + size < buf['size'])
def rb_check_code(buf, size, fields):
    if not rb_check_buf(buf):
        return False
    if (buf['start'] + size > buf['end']) or (size > buf['size']):
        return False
    pos = buf['start'] + size - sizeof_rb_buf_end
    end = from_memory(rb_buf_end_fmt, buf['data'], pos)
    checkcode = rb_crc32(buf, fields)
    if end != checkcode:
        return False
    return True
def rb_set_buf_size(size, rb_val):
    if rb_val['start'] + sizeof_rb_size > rb_val['end']:
        return False
    to_memory(rb_size_fmt, rb_val['data'], rb_val['start'], size)
    return True
def rb_set_field_count(fields, rb_val):
    head_size = rb_field_table_head_size
    if rb_val['start'] + head_size > rb_val['end']:
        return False
    offset = rb_val['start'] + head_size - sizeof_rb_field_size
    to_memory(rb_field_size_fmt, rb_val['data'], offset, fields)
    rb_val['pos'] = rb_val['start'] + rb_seek_field_table_item(fields)
    if rb_val['pos'] > rb_val['end']:
        return False
    return True
def rb_get_field_table_head(rb_val):
    (size, fields) = (0, 0)
    offset = rb_val['start']
    if (offset + rb_field_table_head_size) < rb_val['end']:
        size = from_memory(rb_size_fmt, rb_val['data'], offset)
        fields = from_memory(rb_field_size_fmt, rb_val['data'], offset + sizeof_rb_size)
    return (size, fields)
def rb_set_field_table_item(index, id, offset, rb_val):
    off = rb_val['start'] + rb_seek_field_table_item(index)
    if off + rb_field_table_item_size > rb_val['end']:
        return False
    to_memory(rb_field_id_fmt, rb_val['data'], off, id)
    to_memory(rb_offset_fmt, rb_val['data'], off + sizeof_rb_field_id, offset)
    return True
def rb_get_field_table_item(index, rb_val):
    off = rb_val['start'] + rb_seek_field_table_item(index)
    size = rb_field_table_item_size
    if off + size > rb_val['end']:
        return (0, 0, False)
    id = from_memory(rb_field_id_fmt, rb_val['data'], off)
    offset = from_memory(rb_offset_fmt, rb_val['data'], off + sizeof_rb_field_id)
    return (id, offset, True)
def rb_encode_end(fields, rb_val):
    size = sizeof_rb_buf_end
    if not rb_check_buf(rb_val) or (rb_val['pos'] + size > rb_val['end']):
        return False
    end = rb_crc32(rb_val, fields)
    to_memory(rb_buf_end_fmt, rb_val['data'], rb_val['pos'], end)
    rb_val['pos'] += size
    return True
def rb_seek_array_table_item(index):
    return sizeof_rb_size + index * sizeof_rb_offset
def rb_set_array_count(size, rb_val):
    if not rb_check_buf(rb_val):
        return False
    if rb_val['pos'] + sizeof_rb_size > rb_val['end']:
        return False
    to_memory(rb_size_fmt, rb_val['data'], rb_val['pos'], size)
    rb_val['pos'] = rb_val['start'] + rb_seek_array_table_item(size)
    if rb_val['pos'] > rb_val['end']:
        return False
    return True
def rb_get_array_count(rb_val):
    pos = rb_val['start']
    if pos + sizeof_rb_size < rb_val['end']:
        return from_memory(rb_size_fmt, rb_val['data'], pos)
    return 0
def rb_set_array_table_item(index, offset, rb_val):
    pos = rb_val['start'] + rb_seek_array_table_item(index)
    if pos + sizeof_rb_offset > rb_val['end']:
        return False
    to_memory(rb_offset_fmt, rb_val['data'], pos, offset)
    return True
def rb_get_array_table_item(index, rb_val):
    pos = rb_val['start'] + rb_seek_array_table_item(index)
    if pos + sizeof_rb_offset > rb_val['end']:
        return (0, False)
    return (from_memory(rb_offset_fmt, rb_val['data'], pos), True)

def rb_sizeof_string(obj_val):
    return sizeof_rb_size + len(obj_val)
def rb_encode_string(obj_val, rb_val):
    size = len(obj_val)
    if not rb_encode_check(rb_val, sizeof_rb_size + size):
        return False
    to_memory(rb_size_fmt, rb_val['data'], rb_val['pos'], size)
    rb_val['pos'] += sizeof_rb_size
    if size > 0:
        to_memory(''.join(['<', str(size), 's']) , rb_val['data'], rb_val['pos'], obj_val)
        rb_val['pos'] += size
    return True
def rb_decode_string(rb_val, offset):
    size = sizeof_rb_size
    if not rb_decode_check(rb_val, offset, size):
        return (None, False)
    obj_len = from_memory(rb_size_fmt, rb_val['data'], rb_val['start'] + offset)
    if obj_len > 0:
        off = offset + size
        if not rb_decode_check(rb_val, off, obj_len):
            return (None, False)
        return (from_memory(''.join(['<', str(obj_len), 's']), rb_val['data'], rb_val['start'] + off), True)
    return ('', True)

if __name__ == "__main__":
    pass