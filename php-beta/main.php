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

function test_scalar($setter, $getter, $val, &$buf)
{
    $setter($val, 0, $buf);
    $valout = $getter($buf, 0);
    if ($val != $valout)
    {
        print 'not eq';
    }
}

function test_pack()
{
    $buf = rb_create_buf(8);
    test_scalar(rb_set_bool, rb_get_bool, true, $buf);
    test_scalar(rb_set_int8, rb_get_int8, -120, $buf);
    test_scalar(rb_set_uint8, rb_get_uint8, 120, $buf);
    test_scalar(rb_set_int16, rb_get_int16, -32760, $buf);
    test_scalar(rb_set_uint16, rb_get_uint16, 32760, $buf);
    test_scalar(rb_set_int32, rb_get_int32, -65530, $buf);
    test_scalar(rb_set_uint32, rb_get_uint32, 65530, $buf);
    test_scalar(rb_set_int64, rb_get_int64, -65536, $buf);
    test_scalar(rb_set_uint64, rb_get_uint64, 65536, $buf);
    test_scalar(rb_set_float, rb_get_float, 123.5, $buf);
    test_scalar(rb_set_double, rb_get_double, 999.99999, $buf);
}

function test_create_sample_struct($key)
{
    $obj_val = rb_create_sample_struct();
    $obj_val['int8_val'] = $key;
    $obj_val['uint8_val'] = 128;
    $obj_val['str_val'] = "test_string";
    array_push($obj_val['str_arr_val'], "test_string_1");
    array_push($obj_val['str_arr_val'], "test_string_2");
    array_push($obj_val['str_arr_val'], "test_string_3");
    $obj_val['str_dict_val']["test_key1"] = "test_string_1";
    $obj_val['str_dict_val']["test_key2"] = "test_string_2";
    $obj_val['str_dict_val']["test_key3"] = "test_string_3";
    return $obj_val;
}

function test_sample_struct()
{
    $obj_val = test_create_sample_struct(32);
    $file = "sample_struct.bin";
    rb_dump_sample_struct($obj_val, $file);
    list($obj_out, $rc) = rb_load_sample_struct($file);
    if (!rc)
    {
        return false;
    }
    return rb_eq_sample_struct($obj_val, $obj_out);
}

function test_sample_object()
{   
    $obj_val = rb_create_sample_object();
    $obj_val['obj'] = test_create_sample_struct(8);
    $item1 = test_create_sample_struct(16);
    $item2 = test_create_sample_struct(32);
    $item3 = test_create_sample_struct(64);
    array_push($obj_val['arr'], $item1);
    array_push($obj_val['arr'], $item2);
    array_push($obj_val['arr'], $item3);
    $obj_val['dict']['test_string_1'] = $item1;
    $obj_val['dict']['test_string_2'] = $item2;
    $obj_val['dict']['test_string_3'] = $item3;
    $file = "sample_object.bin";
    rb_dump_sample_object($obj_val, $file);
    list($obj_out, $rc) = rb_load_sample_object($file);
    if (!rc)
    {
        return false;
    }
    return rb_eq_sample_object($obj_val, $obj_out);
}

function init_list(&$obj)
{
    for ($i = 0; $i < 10; $i++)
    {
        array_push($obj, $i);
    }
}

function init_dict(&$obj)
{
    for ($i = 0; $i < 10; $i++)
    {
        $obj[sprintf('key%d', $i)] = sprintf('val%d', $i);
    }
}

function run_perf_test(&$buf, &$obj)
{
    $buf['pos'] = $buf['start'];
    if (!rb_encode_perf_object($obj, $buf))
    {
        printf("rb_encode fail");
        return;
    }
    $buf['pos'] = $buf['start'];
    list($objout, $rc) = rb_decode_perf_object($buf, 0);
    if (!$rc)
    {
        printf("rb_decode fail");
    }
    if (!rb_eq_perf_object($obj, $objout))
    {
        printf("not eq fail");
    }
}

function get_delta($s, $e)
{
    $delta_sec = $e[sec] - $s[sec];
    $delta = $delta_sec * 1000000;
    $delta += ($e[usec] - $s[usec]);
    return $delta;
}

function init_perf_object_base(&$obj)
{
    $obj["bool_val"] = true;
    $obj["int8_val"] = INT8_MIN;
    $obj["uint8_val"] = UINT8_MAX;
    $obj["int16_val"] = INT16_MIN;
    $obj["uint16_val"] = UINT16_MAX;
    $obj["int32_val"] = INT32_MIN;
    $obj["uint32_val"] = UINT32_MAX;
    $obj["int64_val"] = INT64_MIN;
    $obj["uint64_val"] = UINT64_MAX;
    # float has precision issue (IEEE 754)
    $obj["float_val"] = 1024.5;
    $obj["double_val"] = DOUBLE_MAX;
    init_dict($obj["dict_val"]);
}

function perf_test($count)
{
    $obj = rb_create_perf_object();
    init_perf_object_base($obj);
    $obj["str_val"] = "test_string";
    init_list($obj["vec_val"]);
    $buf = rb_create_buf(rb_sizeof_perf_object($obj));
    $start = gettimeofday();
    for ($i = 0; $i < $count; $i++)
    {
        run_perf_test($buf, $obj);
    }
    $end = gettimeofday();
    return get_delta($start, $end);
}

function optional_field_test()
{
    $obj = rb_create_perf_object();
    init_perf_object_base($obj);
    $obj['skip_str_val'] = true;
    $obj['skip_vec_val'] = true;
    
    $file = "optional_field_test.bin";

    rb_dump_perf_object($obj, $file);

    list($obj_out, $rc) = rb_load_perf_object($file);
    if (!rc)
    {
        return false;
    }

    if ($obj_out['rb_has_str_val'])
    {
        printf("error: str_val should be skipped");
    }
    if ($obj_out['rb_has_vec_val'])
    {
        printf("error: vec_val should be skipped");
    }
    return rb_eq_perf_object($obj, $obj_out);
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