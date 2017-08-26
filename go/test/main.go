package main

import (
	"fmt"
	"math"
	"os"
	"strconv"
	"time"

	"github.com/jobs-github/rawbuf/go"
)

func test_init_sample_struct(key int8, obj_val *rawbuf.Sample_struct_t) {
	rawbuf.Rb_init_sample_struct(obj_val)
	obj_val.Int8_val = key
	obj_val.Uint8_val = 128
	obj_val.Str_val = "test_string"
	obj_val.Str_arr_val = rawbuf.String_array_t{}
	obj_val.Str_arr_val = append(obj_val.Str_arr_val, "test_string_1")
	obj_val.Str_arr_val = append(obj_val.Str_arr_val, "test_string_2")
	obj_val.Str_arr_val = append(obj_val.Str_arr_val, "test_string_3")
	obj_val.Str_dict_val = rawbuf.String_dict_t{}
	obj_val.Str_dict_val["test_key1"] = "test_string_1"
	obj_val.Str_dict_val["test_key2"] = "test_string_2"
	obj_val.Str_dict_val["test_key3"] = "test_string_3"
}

func test_sample_struct() bool {
	obj_val := rawbuf.Sample_struct_t{}
	test_init_sample_struct(32, &obj_val)
	file := "sample_struct.bin"
	rawbuf.Rb_dump_sample_struct(&obj_val, file)

	obj_out := rawbuf.Sample_struct_t{}
	rawbuf.Rb_init_sample_struct(&obj_out)
	rawbuf.Rb_load_sample_struct(file, &obj_out)

	return rawbuf.Rb_eq_sample_struct(&obj_val, &obj_out)
}

func test_sample_object() bool {
	obj_val := rawbuf.Sample_object_t{}
	rawbuf.Rb_init_sample_object(&obj_val)
	test_init_sample_struct(8, &obj_val.Obj)

	obj_val.Arr = rawbuf.Sample_struct_array_t{}

	item1 := rawbuf.Sample_struct_t{}
	item2 := rawbuf.Sample_struct_t{}
	item3 := rawbuf.Sample_struct_t{}

	test_init_sample_struct(16, &item1)
	test_init_sample_struct(32, &item2)
	test_init_sample_struct(64, &item3)

	obj_val.Arr = append(obj_val.Arr, &item1)
	obj_val.Arr = append(obj_val.Arr, &item2)
	obj_val.Arr = append(obj_val.Arr, &item3)

	obj_val.Dict = rawbuf.Sample_struct_dict_t{}
	obj_val.Dict["test_string_1"] = &item1
	obj_val.Dict["test_string_2"] = &item2
	obj_val.Dict["test_string_3"] = &item3

	file := "sample_object.bin"
	rawbuf.Rb_dump_sample_object(&obj_val, file)

	obj_out := rawbuf.Sample_object_t{}
	rawbuf.Rb_init_sample_object(&obj_out)
	rawbuf.Rb_load_sample_object(file, &obj_out)

	return rawbuf.Rb_eq_sample_object(&obj_val, &obj_out)
}

func init_int32_array(arr *rawbuf.Int32_array_t) {
	*arr = rawbuf.Int32_array_t{}
	for i := 0; i < 10; i++ {
		*arr = append(*arr, int32(i))
	}
}

func init_string_dict(dict *rawbuf.String_dict_t) {
	*dict = rawbuf.String_dict_t{}
	for i := 0; i < 10; i++ {
		(*dict)[fmt.Sprintf("key%d", i)] = fmt.Sprintf("val%d", i)
	}
}

func init_perf_object_base(obj *rawbuf.Perf_object_t) {
	rawbuf.Rb_init_perf_object(obj)
	obj.Bool_val = true
	obj.Int8_val = math.MinInt8
	obj.Uint8_val = math.MaxUint8
	obj.Int16_val = math.MinInt16
	obj.Uint16_val = math.MaxUint16
	obj.Int32_val = math.MinInt32
	obj.Uint32_val = math.MaxInt32
	obj.Int64_val = math.MinInt64
	obj.Uint64_val = math.MaxUint64
	obj.Float_val = 1024.5
	obj.Double_val = math.MaxFloat64
	init_string_dict(&obj.Dict_val)
}

func init_perf_object(obj *rawbuf.Perf_object_t) {
	init_perf_object_base(obj)
	obj.Str_val = "test_string"
	init_int32_array(&obj.Vec_val)
}

func perf_test_main(obj_val *rawbuf.Perf_object_t, buf *rawbuf.Rb_buf_t) {
	buf.Pos = buf.Start
	if !rawbuf.Rb_encode_perf_object(obj_val, buf) {
		fmt.Printf("rb_encode fail\n")
		return
	}
	obj := rawbuf.Perf_object_t{}
	init_perf_object(&obj)
	buf.Pos = buf.Start
	if !rawbuf.Rb_decode_perf_object(buf, 0, &obj) {
		fmt.Printf("rb_decode fail\n")
		return
	}
	if !rawbuf.Rb_eq_perf_object(obj_val, &obj) {
		fmt.Printf("not eq fail\n")
	}
}

func perf_test(count int64) int64 {
	obj := rawbuf.Perf_object_t{}
	init_perf_object(&obj)
	size := rawbuf.Rb_sizeof_perf_object(&obj)
	buf := rawbuf.Rb_create_buf(size)

	s := time.Now()
	for i := int64(0); i < count; i++ {
		perf_test_main(&obj, buf)
	}
	e := time.Now()

	cost := e.Sub(s)

	return cost.Nanoseconds() / 1000
}

func optional_field_test() bool {
	obj := rawbuf.Perf_object_t{}
	init_perf_object_base(&obj)
	obj.Skip_str_val = true
	obj.Skip_vec_val = true

	file := "optional_field_test.bin"

	rawbuf.Rb_dump_perf_object(&obj, file)

	obj_out := rawbuf.Perf_object_t{}
	rawbuf.Rb_init_perf_object(&obj_out)

	rawbuf.Rb_load_perf_object(file, &obj_out)

	if obj_out.Rb_has_str_val {
		fmt.Printf("error: str_val should be skipped\n")
	}
	if obj_out.Rb_has_vec_val {
		fmt.Printf("error: vec_val should be skipped\n")
	}

	return rawbuf.Rb_eq_perf_object(&obj, &obj_out)
}

func main() {
	if 2 == len(os.Args) {
		count, err := strconv.ParseInt(os.Args[1], 10, 0)
		if err != nil || count < 1 {
			fmt.Printf("invalid argument\n")
			return
		}
		us := perf_test(count)
		qps := int64(float64(1000000) * float64(count) / float64(us))
		fmt.Printf("QPS: %v\n\n", qps)
		return
	}
	if optional_field_test() && test_sample_struct() && test_sample_object() {
		fmt.Printf("unit test passed\n\n")
	}
}
