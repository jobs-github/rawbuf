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

def test_init_sample_struct(key, obj_val):
    obj_val.int8_val.assign(key)
    obj_val.uint8_val.assign(128)
    obj_val.str_val.assign("test_string")
    obj_val.str_arr_val.append(rb_string_t("test_string_1"))
    obj_val.str_arr_val.append(rb_string_t("test_string_2"))
    obj_val.str_arr_val.append(rb_string_t("test_string_3"))
    obj_val.str_dict_val["test_key1"] = rb_string_t("test_string_1");
    obj_val.str_dict_val["test_key2"] = rb_string_t("test_string_2");
    obj_val.str_dict_val["test_key3"] = rb_string_t("test_string_3");

def test_sample_struct():
    obj_val = sample_struct_t()
    test_init_sample_struct(32, obj_val)
    file = "sample_struct.bin"
    obj_val.rb_dump(file)
    obj_out = sample_struct_t()
    obj_out.rb_load(file)
    return (obj_val == obj_out)

def test_sample_object():
    obj_val = sample_object_t()
    test_init_sample_struct(8, obj_val.obj);
    item1 = sample_struct_t()
    item2 = sample_struct_t()
    item3 = sample_struct_t()
    test_init_sample_struct(16, item1)
    test_init_sample_struct(32, item2)
    test_init_sample_struct(64, item3)
    obj_val.arr.append(item1)
    obj_val.arr.append(item2)
    obj_val.arr.append(item3)
    obj_val.dict['test_string_1'] = item1
    obj_val.dict['test_string_2'] = item2
    obj_val.dict['test_string_3'] = item3
    
    file = "sample_object.bin"
    obj_val.rb_dump(file)
    obj_out = sample_object_t()
    obj_out.rb_load(file)
    return obj_val == obj_out

def init_list(obj):
    for i in xrange(10):
        obj.append(rb_int32_t(i))
def init_dict(obj):
    for i in xrange(10):
        key = 'key%d' % i
        val = rb_string_t('val%d' % i)
        obj[key] = val

def init_perf_object_base(obj):
    obj.bool_val.assign(True)
    obj.int8_val.assign(INT8_MIN)
    obj.uint8_val.assign(UINT8_MAX)
    obj.int16_val.assign(INT16_MIN)
    obj.uint16_val.assign(UINT16_MAX)
    obj.int32_val.assign(INT32_MIN)
    obj.uint32_val.assign(UINT32_MAX)
    obj.int64_val.assign(INT64_MIN)
    obj.uint64_val.assign(UINT64_MAX)
    # float has precision issue (IEEE 754)
    obj.float_val.assign(1024.5)
    obj.double_val.assign(DOUBLE_MAX)
    init_dict(obj.dict_val)

class perf_tester_t:
    def __init__(self):
        self.__obj = perf_object_t()
        self.__objout = perf_object_t()
        init_perf_object_base(self.__obj)
        self.__obj.str_val.assign(rb_string_t("test_string"))
        init_list(self.__obj.vec_val)
        self.__buf = rb_create_buf(self.__obj.rb_size())
    def __call__(self):
        self.__buf.pos = self.__buf.start
        if not self.__obj.rb_encode(self.__buf):
            print "rb_encode fail"
            return
        self.__buf.pos = self.__buf.start
        self.__objout.reset()
        if not self.__objout.rb_decode(self.__buf, 0):
            print "rb_decode fail"
        if not (self.__obj == self.__objout):
            print "not eq fail"

def perf_test(count):
    obj = perf_tester_t()
    start = time.time()
    for i in xrange(count):
        obj()
    end = time.time()
    return end - start

def optional_field_test():
    obj = perf_object_t()
    init_perf_object_base(obj)

    obj.skip_str_val();
    obj.skip_vec_val();

    file = "optional_field_test.bin"

    obj.rb_dump(file);

    obj_out = perf_object_t();
    obj_out.rb_load(file);

    if obj_out.rb_has_str_val():
        print "error: str_val should be skipped";
    if obj_out.rb_has_vec_val():
        print "error: vec_val should be skipped"
    return (obj == obj_out)

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