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

#===============================================================================
# private types
#===============================================================================
class rb_types:
    class rb_flags:
        class bool_t:
            bytewidth = 1
            min_val = False
            max_val = True
            py_type = bool
            packer_type = "<b"
        class int8_t:
            bytewidth = 1
            min_val = -(2**7)
            max_val = (2**7) - 1
            py_type = int
            packer_type = "<b"
        class uint8_t:
            bytewidth = 1
            min_val = 0
            max_val = (2**8) - 1
            py_type = int
            packer_type = "<B"
        class int16_t:
            bytewidth = 2
            min_val = -(2**15)
            max_val = (2**15) - 1
            py_type = int
            packer_type = "<h"
        class uint16_t:
            bytewidth = 2
            min_val = 0
            max_val = (2**16) - 1
            py_type = int
            packer_type = "<H"
        class int32_t:
            bytewidth = 4
            min_val = -(2**31)
            max_val = (2**31) - 1
            py_type = int
            packer_type = "<i"
        class uint32_t:
            bytewidth = 4
            min_val = 0
            max_val = (2**32) - 1
            py_type = int
            packer_type = "<I"
        class int64_t:
            bytewidth = 8
            min_val = -(2**63)
            max_val = (2**63) - 1
            py_type = int
            packer_type = "<q"
        class uint64_t:
            bytewidth = 8
            min_val = 0
            max_val = (2**64) - 1
            py_type = int
            packer_type = "<Q"
        class float_t:
            bytewidth = 4
            min_val = None
            max_val = None
            py_type = float
            packer_type = "<f"
        class double_t:
            bytewidth = 8
            min_val = None
            max_val = None
            py_type = float
            packer_type = "<d"
    class rb_number_t:
        def __init__(self, flags, val):
            self.flags = flags
            self.__val = flags.py_type()
            if val is None:
                self.val = self.__val
            else:
                self.__enforce_number(val, flags)
                self.val = val
        def __enforce_number(self, n, flags):
            if flags.min_val is None and flags.max_val is None:
                return
            if not flags.min_val <= n <= flags.max_val:
                raise TypeError("bad number")
        def __eq__(self, other):
            if isinstance(other, rb_types.rb_number_t):
                return self.flags == other.flags and self.val == other.val
            return self.val == other
        def assign(self, other):
            if isinstance(other, rb_types.rb_number_t):
                if self.flags != other.flags:
                    raise TypeError("bad flags")
                self.val = other.val
            else:
                self.val = other
        def reset(self):
            self.val = self.__val
        def rb_size(self):
            return self.flags.bytewidth
        def rb_encode(self, rb_val):
            size = self.rb_size()
            if not rawbuf.rb_encode_check(rb_val, size):
                return False
            rawbuf.to_memory(self.flags.packer_type, rb_val.data, rb_val.pos, self.val)
            rb_val.pos += size
            return True
        def rb_decode(self, rb_val, offset):
            size = self.rb_size()
            if not rawbuf.rb_decode_check(rb_val, offset, size):
                return False
            self.val = rawbuf.from_memory(self.flags.packer_type, rb_val.data, rb_val.start + offset)
            return True
    class rb_scalar_t:
        def __init__(self, flags):
            self.flags = flags
        def rb_size(self):
            return self.flags.bytewidth
        def __call__(self, val = None):
            return rb_types.rb_number_t(self.flags, val)
        def rb_write(self, buf, offset, data):
            rawbuf.to_memory(self.flags.packer_type, buf, offset, data)
            return True
        def rb_read(self, buf, offset):
            return rawbuf.from_memory(self.flags.packer_type, buf, offset)
    class rb_type_pair_t:
        def __init__(self, type_pair = []):
            self.__elem_type = type_pair[0]
            self.__base_type = type_pair[1]
        def create_item(self):
            return self.__elem_type() if None == self.__base_type else self.__elem_type(self.__base_type)

#===============================================================================
# private methods
#===============================================================================
class rawbuf:
    @staticmethod
    def rb_crc32(buf, fields):
        offset = rb_seek_field_table_item(fields)
        tmpbuf = buffer(buf.data, buf.start, offset)
        return ctypes.c_uint32(binascii.crc32(tmpbuf)).value
    @staticmethod
    def from_memory(packer_type, buf, offset):
        return struct.unpack_from(packer_type, buf, offset)[0]
    @staticmethod
    def to_memory(packer_type, buf, offset, data):
        struct.pack_into(packer_type, buf, offset, data)
    @staticmethod
    def rb_check_buf(buf):
        return (buf.size > 0) and (
            buf.pos >= buf.start) and (
            buf.pos <= buf.end) and (
            buf.start + buf.size <= buf.end)
    @staticmethod
    def rb_encode_check(buf, size):
        return rawbuf.rb_check_buf(buf) and (buf.pos + size < buf.end)
    @staticmethod
    def rb_decode_check(buf, offset, size):
        return rawbuf.rb_check_buf(buf) and (
            buf.start + offset + size < buf.end) and (
            offset + size < buf.size)
    @staticmethod
    def rb_make_buf(data, size):
        buf = rb_buf_t()
        buf.data = data
        buf.start = 0
        buf.size = size
        buf.pos = buf.start
        buf.end = buf.start + buf.size
        return buf
    @staticmethod
    def rb_nested_buf(buf, offset):
        nested_buf = rb_buf_t()
        if rawbuf.rb_check_buf(buf):
            nested_buf.data = buf.data
            nested_buf.start = buf.pos if (0 == offset) else (buf.start + offset)
            nested_buf.end = buf.end
            nested_buf.pos = nested_buf.start
            nested_buf.size = nested_buf.end - nested_buf.start
        return nested_buf
    @staticmethod
    def rb_seek_array_table_item(index):
        return rb_size_t.rb_size() + index * rb_offset_t.rb_size()
    @staticmethod
    def rb_set_array_count(size, rb_val):
        if not rawbuf.rb_check_buf(rb_val):
            return False
        if rb_val.pos + rb_size_t.rb_size() > rb_val.end:
            return False
        rb_size_t.rb_write(rb_val.data, rb_val.pos, size)
        rb_val.pos = rb_val.start + rawbuf.rb_seek_array_table_item(size)
        if rb_val.pos > rb_val.end:
            return False
        return True
    @staticmethod
    def rb_get_array_count(rb_val):
        pos = rb_val.start
        if pos + rb_size_t.rb_size() < rb_val.end:
            return rb_size_t.rb_read(rb_val.data, pos)
        return 0
    @staticmethod
    def rb_set_array_table_item(index, offset, rb_val):
        pos = rb_val.start + rawbuf.rb_seek_array_table_item(index)
        if pos + rb_offset_t.rb_size() > rb_val.end:
            return False
        rb_offset_t.rb_write(rb_val.data, pos, offset)
        return True
    @staticmethod
    def rb_get_array_table_item(index, rb_val):
        pos = rb_val.start + rawbuf.rb_seek_array_table_item(index)
        if pos + rb_offset_t.rb_size() > rb_val.end:
            return (False, 0)
        return (True, rb_offset_t.rb_read(rb_val.data, pos)) 
    @staticmethod
    def rb_sizeof_str(obj_val):
        return rb_size_t.rb_size() + len(obj_val)
    @staticmethod
    def rb_encode_str(obj_val, rb_val):
        if not rawbuf.rb_encode_check(rb_val, rawbuf.rb_sizeof_str(obj_val)):
            return False
        size = len(obj_val)
        rb_size_t.rb_write(rb_val.data, rb_val.pos, size)
        rb_val.pos += rb_size_t.rb_size()
        if size > 0:
            packer_t = '<' + str(size) + 's'
            rawbuf.to_memory(packer_t, rb_val.data, rb_val.pos, obj_val)
            rb_val.pos += size
        return True
    @staticmethod
    def rb_decode_str(rb_val, offset):
        size = rb_size_t.rb_size()
        if not rawbuf.rb_decode_check(rb_val, offset, size):
            return (False, '')
        obj_len = rb_size_t.rb_read(rb_val.data, rb_val.start + offset)
        if obj_len > 0:
            off = offset + size
            if not rawbuf.rb_decode_check(rb_val, off, obj_len):
                return (False, '')
            packer_t = '<' + str(obj_len) + 's'
            return (True, rawbuf.from_memory(packer_t, rb_val.data, rb_val.start + off))
        return (True, '')

# public interface
rb_bool_t = rb_types.rb_scalar_t(rb_types.rb_flags.bool_t)
rb_int8_t = rb_types.rb_scalar_t(rb_types.rb_flags.int8_t)
rb_uint8_t = rb_types.rb_scalar_t(rb_types.rb_flags.uint8_t)
rb_int16_t = rb_types.rb_scalar_t(rb_types.rb_flags.int16_t)
rb_uint16_t = rb_types.rb_scalar_t(rb_types.rb_flags.uint16_t)
rb_int32_t = rb_types.rb_scalar_t(rb_types.rb_flags.int32_t)
rb_uint32_t = rb_types.rb_scalar_t(rb_types.rb_flags.uint32_t)
rb_int64_t = rb_types.rb_scalar_t(rb_types.rb_flags.int64_t)
rb_uint64_t = rb_types.rb_scalar_t(rb_types.rb_flags.uint64_t)
rb_float_t = rb_types.rb_scalar_t(rb_types.rb_flags.float_t)
rb_double_t = rb_types.rb_scalar_t(rb_types.rb_flags.double_t)

rb_size_t = rb_uint32_t
rb_field_size_t = rb_uint8_t
rb_field_id_t = rb_field_size_t
rb_offset_t = rb_size_t
rb_buf_end_t = rb_uint32_t

rb_field_table_head_size = rb_size_t.rb_size() + rb_field_size_t.rb_size()
rb_field_table_item_size = rb_field_id_t.rb_size() + rb_offset_t.rb_size()

class rb_buf_t:
    def __init__(self):
        self.size = None
        self.start = None
        self.pos = None
        self.end = None
        self.data = None

def rb_create_buf(size):
    buf = rb_buf_t()
    buf.size = size
    buf.data = bytearray(size)
    buf.start = 0
    buf.pos = buf.start
    buf.end = buf.start + buf.size
    return buf

def rb_seek_field_table_item(index):
    return rb_field_table_head_size + index * rb_field_table_item_size

class rb_string_t:
    def __init__(self, val = ''):
        if not isinstance(val, str):
            raise TypeError("invalid type")
        self.val = val
    def __eq__(self, other):
        if isinstance(other, str):
            return self.val == other
        elif isinstance(other, rb_string_t):
            return self.val == other.val
        else:
            raise TypeError("invalid type")
    def size(self):
        return len(self.val)
    def assign(self, other):
        if isinstance(other, str):
            self.val = other
        elif isinstance(other, rb_string_t):
            self.val = other.val
        else:
            raise TypeError("invalid type")
    def reset(self):
        self.val = ''
    def rb_size(self):
        return rawbuf.rb_sizeof_str(self.val)
    def rb_encode(self, rb_val):
        return rawbuf.rb_encode_str(self.val, rb_val)
    def rb_decode(self, rb_val, offset):
        (rc, self.val) = rawbuf.rb_decode_str(rb_val, offset)
        return rc

class rb_list_t(list):
    def __init__(self, type_pair, value=[]):
        self.__type_pair = rb_types.rb_type_pair_t(type_pair)
        self.assign(value)
    def assign(self, other):
        self[:] = other[:]
    def size(self):
        return len(self)
    def reset(self):
        del self[:]
    def rb_size(self):
        array_count = self.size()
        size = rb_size_t.rb_size() + array_count * rb_size_t.rb_size()
        for item in self:
            size += item.rb_size()
        return size
    def rb_encode(self, rb_val):
        buf = rawbuf.rb_nested_buf(rb_val, 0)
        if buf.size < 1:
            return False
        array_count = self.size()
        if not rawbuf.rb_set_array_count(array_count, buf):
            return False
        for item in self:
            if not rawbuf.rb_set_array_table_item(self.index(item), buf.pos - buf.start, buf):
                return False
            if not item.rb_encode(buf):
                return False
        rb_val.pos = buf.pos
        return True
    def rb_decode(self, rb_val, offset):
        buf = rawbuf.rb_nested_buf(rb_val, offset)
        if buf.size < 1:
            return False
        size = rawbuf.rb_get_array_count(buf)
        if size < 1:
            return True
        for i in xrange(size):
            (rc, off) = rawbuf.rb_get_array_table_item(i, buf)
            if not rc:
                return False
            tmp_obj_val = self.__type_pair.create_item()
            if not tmp_obj_val.rb_decode(buf, off):
                return False
            self.append(tmp_obj_val)
        return True

class rb_dict_t(dict):
    def __init__(self, type_pair, value={}):
        self.__type_pair = rb_types.rb_type_pair_t(type_pair)
        self.update(value)
    def assign(self, other):
        self.update(other)
    def size(self):
        return len(self)
    def reset(self):
        self.clear()
    def rb_size(self):
        array_count = self.size()
        size = rb_size_t.rb_size() + array_count * rb_size_t.rb_size()
        for key in self:
            size += rawbuf.rb_sizeof_str(key)
            size += self[key].rb_size()
        return size
    def rb_encode(self, rb_val):
        buf = rawbuf.rb_nested_buf(rb_val, 0)
        if buf.size < 1:
            return False
        array_count = self.size()
        if not rawbuf.rb_set_array_count(array_count, buf):
            return False
        i = 0
        for key in self:
            if not rawbuf.rb_set_array_table_item(i, buf.pos - buf.start, buf):
                return False
            if not rawbuf.rb_encode_str(key, buf):
                return False
            if not self[key].rb_encode(buf):
                return False
            i += 1
        rb_val.pos = buf.pos
        return True
    def rb_decode(self, rb_val, offset):
        buf = rawbuf.rb_nested_buf(rb_val, offset)
        if buf.size < 1:
            return False
        size = rawbuf.rb_get_array_count(buf)
        if size < 1:
            return True
        for i in xrange(size):
            (rc, off) = rawbuf.rb_get_array_table_item(i, buf)
            if not rc:
                return False
            (rc, key) = rawbuf.rb_decode_str(buf, off)
            if not rc:
                return False
            val = self.__type_pair.create_item()
            if not val.rb_decode(buf, off + rawbuf.rb_sizeof_str(key)):
                return False
            self[key] = val
        return True

def rb_encode_field(index, id, field, buf):
    def rb_set_field_table_item(index, id, offset, rb_val):
        pos = rb_val.start + rb_seek_field_table_item(index)
        size = rb_field_table_item_size
        if pos + size > rb_val.end:
            return False
        rb_field_id_t.rb_write(rb_val.data, pos, id)
        rb_offset_t.rb_write(rb_val.data, pos + rb_field_id_t.rb_size(), offset)
        return True
    if not rb_set_field_table_item(index, id, buf.pos - buf.start, buf):
        return False
    if not field.rb_encode(buf):
        return False
    return True

def rb_decode_field(field_id, id, offset, rb_val, rc, rb_has_field, field):
    if id == field_id:
        rc.val = field.rb_decode(rb_val, offset)
        if rc.val:
            rb_has_field.val = True
        return True
    return False

def rb_encode_base(obj_val, rb_val):
    def rb_set_buf_size(size, rb_val):
        if rb_val.start + rb_size_t.rb_size() > rb_val.end:
            return False
        rb_size_t.rb_write(rb_val.data, rb_val.start, size)
        return True
    def rb_set_field_count(fields, rb_val):
        head_size = rb_field_table_head_size
        if rb_val.start + head_size > rb_val.end:
            return False
        offset = rb_val.start + head_size - rb_field_size_t.rb_size()
        rb_field_size_t.rb_write(rb_val.data, offset, fields)
        rb_val.pos = rb_val.start + rb_seek_field_table_item(fields)
        if rb_val.pos > rb_val.end:
            return False
        return True
    def rb_encode_end(fields, rb_val):
        size = rb_buf_end_t.rb_size()
        if not rawbuf.rb_check_buf(rb_val) or (rb_val.pos + size > rb_val.end):
            return False
        end = rawbuf.rb_crc32(rb_val, fields)
        rb_buf_end_t.rb_write(rb_val.data, rb_val.pos, end)
        rb_val.pos += size
        return True
    buf = rawbuf.rb_nested_buf(rb_val, 0)
    if buf.size < 1:
        return False
    fields = obj_val.rb_fields()
    if not rb_set_field_count(fields, buf):
        return False
    if not obj_val.encode(buf):
        return False
    if not rb_set_buf_size(buf.pos - buf.start + rb_buf_end_t.rb_size(), buf):
        return False
    if not rb_encode_end(fields, buf):
        return False
    rb_val.pos = buf.pos
    return True

def rb_decode_base(rb_val, offset, obj_val):
    def rb_check_code(buf, size, fields):
        if not rawbuf.rb_check_buf(buf):
            return False
        if (buf.start + size > buf.end) or (size > buf.size):
            return False
        pos = buf.start + size - rb_buf_end_t.rb_size()
        end = rb_buf_end_t.rb_read(buf.data, pos)
        checkcode = rawbuf.rb_crc32(buf, fields)
        if end != checkcode:
            return False
        return True
    buf = rawbuf.rb_nested_buf(rb_val, offset)
    if buf.size < 1:
        return False
    if not rawbuf.rb_decode_check(buf, 0, rb_field_table_head_size):
        return False
    buf_size = rb_size_t.rb_read(buf.data, buf.start)
    fields = rb_field_size_t.rb_read(buf.data, buf.start + rb_size_t.rb_size())
    if fields < 1 or not rb_check_code(buf, buf_size, fields):
        return False
    for i in xrange(fields):
        pos = buf.start + rb_seek_field_table_item(i)
        size = rb_field_table_item_size
        if pos + size > buf.end:
            return False
        field_id = rb_field_id_t.rb_read(buf.data, pos)
        field_off = rb_offset_t.rb_read(buf.data, pos + rb_field_id_t.rb_size())
        if field_off >= buf_size:
            return False
        if field_off > 0 and not obj_val.decode(field_id, field_off, buf):
            return False
    return True

def rb_dump_base(obj_val, path):
    class rb_wbuf_t:
        def __init__(self, path, size):
            with open(path, 'wb') as f:
                f.seek(f.tell() + size - 1)
                f.write('\0')
            self.__fd = open(path, 'rb+')
            self.__mm = mmap.mmap(self.__fd.fileno(), 0, access=mmap.ACCESS_WRITE)
        def __enter__(self):
            return self.__mm
        def __exit__(self, exception_type, exception_val, trace):
            self.__mm.close()
            self.__fd.close()
    size = obj_val.rb_size()
    if size < 1:
        return False
    with rb_wbuf_t(path, size) as data:
        buf = rawbuf.rb_make_buf(data, size)
        return obj_val.rb_encode(buf)
    return False

def rb_load_base(path, obj_val):
    class rb_rbuf_t:
        def __init__(self, path, size):
            self.__fd = open(path, 'rb')
            self.__mmap = mmap.mmap(self.__fd.fileno(), 0, access=mmap.ACCESS_READ)
        def __enter__(self):
            return self.__mmap
        def __exit__(self, exception_type, exception_val, trace):
            self.__mmap.close()
            self.__fd.close()
    file_size = os.stat(path).st_size
    with rb_rbuf_t(path, file_size) as data:
        size = rb_size_t.rb_read(data, 0)
        if size < 1 or size > file_size:
            return False
        buf = rawbuf.rb_make_buf(data, size)
        return obj_val.rb_decode(buf, 0)
    return False

if __name__ == "__main__":
    pass