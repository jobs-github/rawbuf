#include <stdio.h>
#ifdef WIN32
    #define true  1
    #define false 0
#else
    #include <stdbool.h>
#endif

#ifdef WIN32
    #pragma warning(disable: 4005)
    #pragma warning(disable: 4244)
    #include <time.h>
    #include <Windows.h>
    #define INT64_MIN  LLONG_MIN
    #define UINT64_MAX ULLONG_MAX
#elif __APPLE__
    #include <sys/time.h>
    typedef suseconds_t __suseconds_t;
#else
    #include <sys/time.h>
    #define INT64_MIN   LONG_LONG_MIN
    #define UINT64_MAX  ULONG_LONG_MAX
#endif // WIN32

#include "sample_test.h"
#include "perf_test.h"

void test_init_sample_struct(int8_t key, sample_struct_t * obj_val)
{
    rb_init_sample_struct(obj_val);
    obj_val->int8_val = key;
    obj_val->uint8_val = 128;

    obj_val->str_val = rb_create_string("test_string");

    rb_str_t s1 = rb_make_str("test_string_1");
    rb_str_t s2 = rb_make_str("test_string_2");
    rb_str_t s3 = rb_make_str("test_string_3");
    obj_val->str_arr_val = rb_create_string_array(3);
    rb_append_to_string_array(&s1, &obj_val->str_arr_val);
    rb_append_to_string_array(&s2, &obj_val->str_arr_val);
    rb_append_to_string_array(&s3, &obj_val->str_arr_val);

    rb_str_t k1 = rb_make_str("test_key1");
    rb_str_t k2 = rb_make_str("test_key2");
    rb_str_t k3 = rb_make_str("test_key3");

    rb_str_t v1 = rb_make_str("test_string_1");
    rb_str_t v2 = rb_make_str("test_string_2");
    rb_str_t v3 = rb_make_str("test_string_3");

    obj_val->str_dict_val = rb_create_string_dict(3);
    rb_string_dict_set_item(&k1, &v1, &obj_val->str_dict_val);
    rb_string_dict_set_item(&k2, &v2, &obj_val->str_dict_val);
    rb_string_dict_set_item(&k3, &v3, &obj_val->str_dict_val);
}

rb_bool_t test_sample_struct()
{
    sample_struct_t obj_val;
    test_init_sample_struct(32, &obj_val);

    const char * file = "sample_struct.bin";

    rb_dump_sample_struct(&obj_val, file);

    sample_struct_t obj_out;
    rb_init_sample_struct(&obj_out);
    rb_load_sample_struct(file, &obj_out);

    rb_bool_t eq = rb_eq_sample_struct(&obj_val, &obj_out);

    rb_dispose_sample_struct(&obj_val);
    rb_dispose_sample_struct(&obj_out);

    return eq;
}

rb_bool_t test_sample_object()
{
    sample_object_t obj_val;
    rb_init_sample_object(&obj_val);

    test_init_sample_struct(8, &obj_val.obj);

    obj_val.arr = rb_create_sample_struct_array(3);

    sample_struct_t item1, item2, item3;
    test_init_sample_struct(16, &item1);
    test_init_sample_struct(32, &item2);
    test_init_sample_struct(64, &item3);

    rb_append_to_sample_struct_array(&item1, &obj_val.arr);
    rb_append_to_sample_struct_array(&item2, &obj_val.arr);
    rb_append_to_sample_struct_array(&item3, &obj_val.arr);

    rb_str_t k1 = rb_make_str("test_string_1");
    rb_str_t k2 = rb_make_str("test_string_2");
    rb_str_t k3 = rb_make_str("test_string_3");

    obj_val.dict = rb_create_sample_struct_dict(3);
    rb_sample_struct_dict_set_item(&k1, &item1, &obj_val.dict);
    rb_sample_struct_dict_set_item(&k2, &item2, &obj_val.dict);
    rb_sample_struct_dict_set_item(&k3, &item3, &obj_val.dict);

    rb_dispose_sample_struct(&item1);
    rb_dispose_sample_struct(&item2);
    rb_dispose_sample_struct(&item3);

    const char * file = "sample_object.bin";

    rb_dump_sample_object(&obj_val, file);

    sample_object_t obj_out;
    rb_init_sample_object(&obj_out);
    rb_load_sample_object(file, &obj_out);

    rb_bool_t eq = rb_eq_sample_object(&obj_val, &obj_out);

    rb_dispose_sample_object(&obj_val);
    rb_dispose_sample_object(&obj_out);

    return eq;
}

void init_int32_array(int32_array_t * arr)
{
    *arr = rb_create_int32_array(10);
    int i = 0;
    for (i = 0; i < 10; ++i)
    {
        rb_append_to_int32_array(&i, arr);
    }
}

void init_string_dict(string_dict_t * dict)
{
    *dict = rb_create_string_dict(10);
    int i = 0;
    for (i = 0; i < 10; ++i)
    {
        char key[32];
        sprintf(key, "key%d", i);
        char val[32];
        sprintf(val, "val%d", i);
        rb_str_t k = { strlen(key), key };
        rb_str_t v = { strlen(val), val };
        rb_string_dict_set_item(&k, &v, dict);
    }
}

void init_perf_object_base(perf_object_t * obj)
{
    rb_init_perf_object(obj);
    obj->bool_val = true;
    obj->int8_val = SCHAR_MIN;
    obj->uint8_val = UCHAR_MAX;
    obj->int16_val = SHRT_MIN;
    obj->uint16_val = USHRT_MAX;
    obj->int32_val = INT_MIN;
    obj->uint32_val = UINT_MAX;
    obj->int64_val = INT64_MIN;
    obj->uint64_val = UINT64_MAX;
    obj->float_val = 1024.5;
    obj->double_val = DBL_MAX;
    init_string_dict(&obj->dict_val);
}

void init_perf_object(perf_object_t * obj)
{
    init_perf_object_base(obj);
    obj->str_val = rb_create_string("test_string");
    init_int32_array(&obj->vec_val);
}

void perf_test_main(const perf_object_t * obj_val, rb_buf_t * buf)
{
    buf->pos = buf->start;
    if (!rb_encode_perf_object(obj_val, buf))
    {
        printf("rb_encode fail\n");
        return;
    }
    perf_object_t obj;
    init_perf_object(&obj);
    buf->pos = buf->start;
    if (!rb_decode_perf_object(buf, 0, &obj))
    {
        printf("rb_decode fail\n");
        return;
    }
    if (!rb_eq_perf_object(obj_val, &obj))
    {
        printf("not eq fail\n");
    }
    rb_dispose_perf_object(&obj);
}

#ifdef WIN32

int64_t perf_test(int count)
{
    LARGE_INTEGER freq={0};
    QueryPerformanceFrequency(&freq); 

    perf_object_t obj;
    init_perf_object(&obj);
    rb_size_t len = rb_sizeof_perf_object(&obj);
    rb_buf_t buf = rb_create_buf(len);

    LARGE_INTEGER s = {0};
    QueryPerformanceCounter(&s);

    int i = 0;
    for (i = 0; i < count; ++i)
    {
        perf_test_main(&obj, &buf);
    }
    LARGE_INTEGER e = {0};
    QueryPerformanceCounter(&e);

    rb_dispose_buf(&buf);
    rb_dispose_perf_object(&obj);

    return ( ((e.QuadPart - s.QuadPart) * 1000000)/freq.QuadPart);
}

#else

__suseconds_t get_delta(struct  timeval * s, struct  timeval * e)
{
    time_t delta_sec = e->tv_sec - s->tv_sec;
    __suseconds_t delta = delta_sec * 1000000;
    delta += (e->tv_usec - s->tv_usec);
    return delta;
}

int64_t perf_test(int count)
{
    perf_object_t obj;
    init_perf_object(&obj);
    rb_size_t len = rb_sizeof_perf_object(&obj);
    rb_buf_t buf = rb_create_buf(len);

    struct  timeval    s, e;
    struct  timezone   tz;
    gettimeofday(&s, &tz);
    int i = 0;
    for (i = 0; i < count; ++i)
    {
        perf_test_main(&obj, &buf);
    }
    gettimeofday(&e, &tz);

    rb_dispose_buf(&buf);
    rb_dispose_perf_object(&obj);

    return get_delta(&s, &e);
}

#endif

rb_bool_t optional_field_test()
{
    perf_object_t obj;
    init_perf_object_base(&obj);
    obj.skip_str_val = true;
    obj.skip_vec_val = true;

    const char * file = "optional_field_test.bin";

    rb_dump_perf_object(&obj, file);

    perf_object_t obj_out;
    rb_init_perf_object(&obj_out);

    rb_load_perf_object(file, &obj_out);

    if (obj_out.rb_has_str_val)
    {
        printf("error: str_val should be skipped\n");
    }
    if (obj_out.rb_has_vec_val)
    {
        printf("error: vec_val should be skipped\n");
    }

    rb_bool_t eq = rb_eq_perf_object(&obj, &obj_out);

    return eq;
}

int main(int argc, char * argv[])
{
    if (2 == argc)
    {
        int count = atoi(argv[1]);
        if (count < 1)
        {
            printf("invalid argument\n");
            return 0;
        }
        int64_t us = perf_test(count);
        int64_t qps = (int64_t)((double) 1000000 * (double) count / (double) us);
#ifdef __APPLE__
        printf("QPS: %lld\n\n", qps);
#else
        printf("QPS: %ld\n\n", qps);
#endif
        return 0;
    }

    if (optional_field_test() && test_sample_struct() && test_sample_object())
    {
        printf("unit test passed\n\n");
    }
    return 0;
}
