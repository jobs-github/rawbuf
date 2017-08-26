#include <stdio.h>

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

void test_init_sample_struct(int8_t key, rawbuf::sample_struct_t& obj_val)
{
    obj_val.int8_val = key;
    obj_val.uint8_val = 128;

    obj_val.str_val.assign("test_string");

    obj_val.str_arr_val.push_back("test_string_1");
    obj_val.str_arr_val.push_back("test_string_2");
    obj_val.str_arr_val.push_back("test_string_3");

    obj_val.str_dict_val["test_key1"] = "test_string_1";
    obj_val.str_dict_val["test_key2"] = "test_string_2";
    obj_val.str_dict_val["test_key3"] = "test_string_3";
}

bool test_sample_struct()
{
    rawbuf::sample_struct_t obj_val;

    test_init_sample_struct(32, obj_val);

    const char * file = "sample_struct.bin";

    rawbuf::rb_dump(obj_val, file);

    rawbuf::sample_struct_t obj_out;
    rawbuf::rb_load(file, obj_out);

    bool eq = (obj_val == obj_out);

    return eq;
}

bool test_sample_object()
{
    rawbuf::sample_object_t obj_val;
    test_init_sample_struct(8, obj_val.obj);

    rawbuf::sample_struct_t item1, item2, item3;
    test_init_sample_struct(16, item1);
    test_init_sample_struct(32, item2);
    test_init_sample_struct(64, item3);

    obj_val.arr.push_back(item1);
    obj_val.arr.push_back(item2);
    obj_val.arr.push_back(item3);

    obj_val.dict["test_string_1"] = item1;
    obj_val.dict["test_string_2"] = item2;
    obj_val.dict["test_string_3"] = item3;

    const char * file = "sample_object.bin";

    rawbuf::rb_dump(obj_val, file);

    rawbuf::sample_object_t obj_out;
    rawbuf::rb_load(file, obj_out);

    bool eq = (obj_val == obj_out);

    return eq;
}

namespace rawbuf {

template <typename T>
void init(std::vector<T>& obj)
{
    for (int i = 0; i < 10; ++i)
    {
        obj.push_back(i);
    }
}

void init(std::map<std::string, std::string>& obj)
{
    for (int i = 0; i < 10; ++i)
    {
        char key[32];
        sprintf(key, "key%d", i);
        char val[32];
        sprintf(val, "val%d", i);

        obj[key] = val;
    }
}

void init_perf_object_base(perf_object_t& obj)
{
    obj.bool_val = true;
    obj.int8_val = SCHAR_MIN;
    obj.uint8_val = UCHAR_MAX;
    obj.int16_val = SHRT_MIN;
    obj.uint16_val = USHRT_MAX;
    obj.int32_val = INT_MIN;
    obj.uint32_val = UINT_MAX;
    obj.int64_val = INT64_MIN;
    obj.uint64_val = UINT64_MAX;
    obj.float_val = 1024.5;
    obj.double_val = DBL_MAX;
    init(obj.dict_val);
}

struct perf_tester_t
{
    perf_tester_t()
    {
        init_perf_object_base(obj_);
        obj_.str_val = "test_string";
        init(obj_.vec_val);
        len_ = rb_sizeof(obj_);
        buf_ = rb_create_buf(len_);
    }
    ~perf_tester_t()
    {
        rb_dispose_buf(buf_);
    }
    void operator()()
    {
        buf_.pos = buf_.start;
        if (!rb_encode(obj_, buf_))
        {
            printf("rb_encode fail\n");
            return;
        }
        rawbuf::perf_object_t obj;
        buf_.pos = buf_.start;
        if (!rb_decode(buf_, 0, obj))
        {
            printf("rb_decode fail\n");
            return;
        }
        if (!(obj_ == obj))
        {
            printf("not eq fail\n");
        }
    }
private:
    perf_object_t obj_;
    rb_size_t len_;
    rb_buf_t buf_;
};

#ifdef WIN32

int64_t perf_test(int count)
{
    LARGE_INTEGER freq={0};
    QueryPerformanceFrequency(&freq); 

    perf_tester_t obj;

    LARGE_INTEGER s = {0};
    QueryPerformanceCounter(&s);

    int i = 0;
    for (i = 0; i < count; ++i)
    {
        obj();
    }
    LARGE_INTEGER e = {0};
    QueryPerformanceCounter(&e);

    return ( ((e.QuadPart - s.QuadPart) * 1000000)/freq.QuadPart);
}

#else

__suseconds_t get_current_time()
{
    struct  timeval    tv;
    struct  timezone   tz;
    gettimeofday(&tv,&tz);

    return tv.tv_usec;
}

__suseconds_t get_delta(struct  timeval& s, struct  timeval& e)
{
    time_t delta_sec = e.tv_sec - s.tv_sec;
    __suseconds_t delta = delta_sec * 1000000;
    delta += (e.tv_usec - s.tv_usec);
    return delta;
}

__suseconds_t perf_test(int count)
{
    perf_tester_t obj;
    struct  timeval    s, e;
    struct  timezone   tz;
    gettimeofday(&s, &tz);
    for (int i = 0; i < count; ++i)
    {
        obj();
    }
    gettimeofday(&e, &tz);

    return get_delta(s, e);
}

#endif

} // rawbuf

bool optional_field_test()
{
    rawbuf::perf_object_t obj;
    rawbuf::init_perf_object_base(obj);
    obj.skip_str_val();
    obj.skip_vec_val();

    const char * file = "optional_field_test.bin";

    rawbuf::rb_dump(obj, file);

    rawbuf::perf_object_t obj_out;
    rawbuf::rb_load(file, obj_out);

    if (obj_out.rb_has_str_val())
    {
        printf("error: str_val should be skipped\n");
    }
    if (obj_out.rb_has_vec_val())
    {
        printf("error: vec_val should be skipped\n");
    }

    bool eq = (obj == obj_out);

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
        int64_t us = rawbuf::perf_test(count);
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
