#!/usr/bin/python
import sys
import time
from sample_test import *
from perf_test import *

INT8_MIN = -(2**7)
UINT8_MAX = (2**8) - 1
INT16_MIN = -(2**15)
UINT16_MAX = (2**16) - 1
INT32_MIN = -(2**31)
UINT32_MAX = (2**32) - 1
INT64_MIN = -(2**63)
UINT64_MAX = (2**64) - 1
#FLOAT_MAX = 3.40282e+038
DOUBLE_MAX = 1.79769e+308

def test_create_sample_struct(key):
    obj_val = rb_create_sample_struct()
    obj_val['int8_val'] = key
    obj_val['uint8_val'] = 128
    obj_val['str_val'] = "test_string"
    obj_val['str_arr_val'].append("test_string_1")
    obj_val['str_arr_val'].append("test_string_2")
    obj_val['str_arr_val'].append("test_string_3")
    obj_val['str_dict_val']["test_key1"] = "test_string_1"
    obj_val['str_dict_val']["test_key2"] = "test_string_2"
    obj_val['str_dict_val']["test_key3"] = "test_string_3"
    return obj_val
 
def test_sample_struct():
    obj_val = test_create_sample_struct(32)
    file = "sample_struct.bin"
    rb_dump_sample_struct(obj_val, file)
    (obj_out, rc) = rb_load_sample_struct(file)
    if not rc:
        return False
    return rb_eq_sample_struct(obj_val, obj_out)

def test_sample_object():
    obj_val = rb_create_sample_object()
    obj_val['obj'] = test_create_sample_struct(8)
    item1 = test_create_sample_struct(16)
    item2 = test_create_sample_struct(32)
    item3 = test_create_sample_struct(64)
    obj_val['arr'].append(item1)
    obj_val['arr'].append(item2)
    obj_val['arr'].append(item3)
    obj_val['dict']['test_string_1'] = item1
    obj_val['dict']['test_string_2'] = item2
    obj_val['dict']['test_string_3'] = item3
    file = "sample_object.bin"
    rb_dump_sample_object(obj_val, file)
    (obj_out, rc) = rb_load_sample_object(file)
    if not rc:
        return False
    return rb_eq_sample_object(obj_val, obj_out)

def init_list(obj):
    for i in xrange(10):
        obj.append(i)
def init_dict(obj):
    for i in xrange(10):
        obj['key%d' % i] = 'val%d' % i

def run_perf_test(buf, obj):
    buf['pos'] = buf['start']
    if not rb_encode_perf_object(obj, buf):
        print "rb_encode fail"
        return
    buf['pos'] = buf['start']
    (objout, rc) = rb_decode_perf_object(buf, 0)
    if not rc:
        print "rb_decode fail"
    if not rb_eq_perf_object(obj, objout):
        print "not eq fail"

def init_perf_object_base(obj):
    obj["bool_val"] = True
    obj["int8_val"] = INT8_MIN
    obj["uint8_val"] = UINT8_MAX
    obj["int16_val"] = INT16_MIN
    obj["uint16_val"] = UINT16_MAX
    obj["int32_val"] = INT32_MIN
    obj["uint32_val"] = UINT32_MAX
    obj["int64_val"] = INT64_MIN
    obj["uint64_val"] = UINT64_MAX
    # float has precision issue (IEEE 754)
    obj["float_val"] = 1024.5
    obj["double_val"] = DOUBLE_MAX
    init_dict(obj["dict_val"])

def perf_test(count):
    obj = rb_create_perf_object()
    init_perf_object_base(obj)
    obj["str_val"] = "test_string"
    init_list(obj["vec_val"])
    buf = rb_create_buf(rb_sizeof_perf_object(obj))
    start = time.time()
    for i in xrange(count):
        run_perf_test(buf, obj)
    end = time.time()
    return end - start
 
def optional_field_test():
    obj = rb_create_perf_object()
    init_perf_object_base(obj)
    obj['skip_str_val'] = True
    obj['skip_vec_val'] = True
 
    file = "optional_field_test.bin"
    
    rb_dump_perf_object(obj, file)
 
    (obj_out, rc) = rb_load_perf_object(file)
    if not rc:
        return False
 
    if obj_out['rb_has_str_val']:
        print "error: str_val should be skipped";
    if obj_out['rb_has_vec_val']:
        print "error: vec_val should be skipped"
    return rb_eq_perf_object(obj, obj_out)

def test_main(argv):
    if 2 == len(argv):
        count = int(argv[1])
        if count < 1:
            print 'invalid argument'
            return
        us = perf_test(count)
        qps = int(count / us)
        print 'QPS: %d' % qps
        return
    if optional_field_test() and test_sample_struct() and test_sample_object():
        print 'unit test passed'
if __name__ == "__main__":
    test_main(sys.argv)