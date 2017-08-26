<?php
ini_set('error_reporting', E_ALL & ~E_NOTICE & ~E_WARNING);

require 'sample_test.php';
require 'perf_test.php';

define("INT8_MIN", -128);
define("UINT8_MAX", 255);
define("INT16_MIN", -32768);
define("UINT16_MAX", 65535);
define("INT32_MIN", -2147483648);
define("UINT32_MAX", 4294967295);
define("INT64_MIN", PHP_INT_MIN);
define("UINT64_MAX", PHP_INT_MAX);
define("FLOAT_MAX", 3.40282e+038);
define("DOUBLE_MAX", 1.79769e+308);

function test_scalar($flags, $val, $buf)
{
    rawbuf::to_memory($flags::$writer, $flags::$bytewidth, $buf, 0, $val);
    $valout = rawbuf::from_memory($flags::$reader, $flags::$bytewidth, $buf, 0);
    if ($val != $valout)
    {
        print 'not eq';
    }
}

function test_pack()
{
    $buf = rb_create_buf(8);
    test_scalar(bool_flags_t, true, $buf);
    test_scalar(int8_flags_t, -120, $buf);
    test_scalar(uint8_flags_t, 120, $buf);
    test_scalar(int16_flags_t, -32760, $buf);
    test_scalar(uint16_flags_t, 32760, $buf);
    test_scalar(int32_flags_t, -65530, $buf);
    test_scalar(uint32_flags_t, 65530, $buf);
    test_scalar(int64_flags_t, -65536, $buf);
    test_scalar(uint64_flags_t, 65536, $buf);
    test_scalar(float_flags_t, 123.5, $buf);
    test_scalar(double_flags_t, 999.99999, $buf);
}

function test_init_sample_struct($key, $obj_val)
{
    $obj_val->int8_val->assign($key);
    $obj_val->uint8_val->assign(128);
    $obj_val->str_val->assign("test_string");
    $obj_val->str_arr_val->append(new rb_string_t("test_string_1"));
    $obj_val->str_arr_val->append(new rb_string_t("test_string_2"));
    $obj_val->str_arr_val->append(new rb_string_t("test_string_3"));
    $obj_val->str_dict_val["test_key1"] = new rb_string_t("test_string_1");
    $obj_val->str_dict_val["test_key2"] = new rb_string_t("test_string_2");
    $obj_val->str_dict_val["test_key3"] = new rb_string_t("test_string_3");
}

function test_sample_struct()
{
    $obj_val = new sample_struct_t();
    test_init_sample_struct(32, $obj_val);
    $file = "sample_struct.bin";
    $obj_val->rb_dump($file);
    $obj_out = new sample_struct_t();
    $obj_out->rb_load($file);
    return $obj_val->eq($obj_out);
}

function test_sample_object()
{
    $obj_val = new sample_object_t();
    test_init_sample_struct(8, $obj_val->obj);
    $item1 = new sample_struct_t();
    $item2 = new sample_struct_t();
    $item3 = new sample_struct_t();
    test_init_sample_struct(16, $item1);
    test_init_sample_struct(32, $item2);
    test_init_sample_struct(64, $item3);
    $obj_val->arr->append($item1);
    $obj_val->arr->append($item2);
    $obj_val->arr->append($item3);
    $obj_val->dict["test_string_1"] = $item1;
    $obj_val->dict["test_string_2"] = $item2;
    $obj_val->dict["test_string_3"] = $item3;
    
    $file = "sample_object.bin";
    $obj_val->rb_dump($file);
    $obj_out = new sample_object_t();
    $obj_out->rb_load($file);
    return $obj_val->eq($obj_out);
}

function init_list($obj)
{
    for ($i = 0; $i < 10; ++$i)
    {
        $obj->append(new rb_int32_t($i));
    }
}

function init_dict($obj)
{
    for ($i = 0; $i < 10; ++$i)
    {
        $key = sprintf('key%d', $i);
        $val = new rb_string_t(sprintf('val%d', $i));
        $obj[$key] = $val;
    }
}

function init_perf_object_base($obj)
{
    $obj->bool_val->assign(true);
    $obj->int8_val->assign(INT8_MIN);
    $obj->uint8_val->assign(UINT8_MAX);
    $obj->int16_val->assign(INT16_MIN);
    $obj->uint16_val->assign(UINT16_MAX);
    $obj->int32_val->assign(INT32_MIN);
    $obj->uint32_val->assign(UINT32_MAX);
    $obj->int64_val->assign(INT64_MIN);
    $obj->uint64_val->assign(UINT64_MAX);
    # float has precision issue (IEEE 754)
    $obj->float_val->assign(1024.5);
    $obj->double_val->assign(DOUBLE_MAX);
    init_dict($obj->dict_val);
}

class perf_tester_t
{
    private $obj = null;
    private $obj_out = null;
    private $buf = null;
    public function __construct()
    {
        $this->obj = new perf_object_t();
        $this->obj_out = new perf_object_t();
        init_perf_object_base($this->obj);
        $this->obj->str_val->assign(new rb_string_t("test_string"));
        init_list($this->obj->vec_val);
        $this->buf = rb_create_buf($this->obj->rb_size());
    }
    public function __invoke()
    {
        $this->buf->pos = $this->buf->start;
        if (!$this->obj->rb_encode($this->buf))
        {
            printf("rb_encode fail\n");
            return;
        }
        $this->buf->pos = $this->buf->start;
        $this->obj_out->reset();
        if (!$this->obj_out->rb_decode($this->buf, 0))
        {
            printf("rb_decode fail\n");
        }
        if (!($this->obj->eq($this->obj_out)))
        {
            printf("not eq fail\n");
        }
    }
    
}

function get_delta($s, $e)
{
    $delta_sec = $e[sec] - $s[sec];
    $delta = $delta_sec * 1000000;
    $delta += ($e[usec] - $s[usec]);
    return $delta;
}

function perf_test($count)
{
    $obj = new perf_tester_t();
    $start = gettimeofday();
    for ($i = 0; $i < $count; ++$i)
    {
        $obj();
    }
    $end = gettimeofday();
    return get_delta($start, $end);
}

function optional_field_test()
{
    $obj = new perf_object_t();
    init_perf_object_base($obj);
    $obj->skip_str_val();
    $obj->skip_vec_val();

    $file = "optional_field_test.bin";

    $obj->rb_dump($file);

    $obj_out = new perf_object_t();
    $obj_out->rb_load($file);

    if ($obj_out->rb_has_str_val())
    {
        printf("error: str_val should be skipped\n");
    }
    if ($obj_out->rb_has_vec_val())
    {
        printf("error: vec_val should be skipped\n");
    }

    return ($obj->eq($obj_out));
}

function main($argc, $argv)
{
    if (2 == $argc)
    {
        $count = intval($argv[1]);
        if ($count < 1)
        {
            printf("invalid argument\n");
            return;
        }
        $us = perf_test($count);
        $qps = intval(1000000.0 * floatval($count) / floatval($us));
        printf("QPS: %ld\n\n", $qps);
        return;
    }

    test_pack();
    
    if (optional_field_test() && test_sample_struct() && test_sample_object())
    {
        printf("unit test passed\n\n");
    }
}

main($argc, $argv);

?>