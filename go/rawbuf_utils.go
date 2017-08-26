package rawbuf

import (
	"hash/crc32"
	"math"
	"os"
	"unsafe"

	"github.com/edsrzf/mmap-go"
)

type Rb_size_t uint32
type Rb_field_size_t uint8
type Rb_field_id_t Rb_field_size_t
type Rb_offset_t Rb_size_t
type Rb_buf_end_t uint32

var (
	Sizeof_int8    = Rb_size_t(unsafe.Sizeof(int8(0)))
	Sizeof_uint8   = Rb_size_t(unsafe.Sizeof(uint8(0)))
	Sizeof_int16   = Rb_size_t(unsafe.Sizeof(int16(0)))
	Sizeof_uint16  = Rb_size_t(unsafe.Sizeof(uint16(0)))
	Sizeof_int32   = Rb_size_t(unsafe.Sizeof(int32(0)))
	Sizeof_uint32  = Rb_size_t(unsafe.Sizeof(uint32(0)))
	Sizeof_int64   = Rb_size_t(unsafe.Sizeof(int64(0)))
	Sizeof_uint64  = Rb_size_t(unsafe.Sizeof(uint64(0)))
	Sizeof_bool    = Sizeof_int8
	Sizeof_float32 = Rb_size_t(unsafe.Sizeof(float32(0)))
	Sizeof_float64 = Rb_size_t(unsafe.Sizeof(float64(0)))
)

var (
	Sizeof_rb_size       = Rb_size_t(unsafe.Sizeof(Rb_size_t(0)))
	Sizeof_rb_field_size = Rb_size_t(unsafe.Sizeof(Rb_field_size_t(0)))
	Sizeof_rb_field_id   = Rb_size_t(unsafe.Sizeof(Rb_field_id_t(0)))
	Sizeof_rb_offset     = Rb_size_t(unsafe.Sizeof(Rb_offset_t(0)))
	Sizeof_rb_buf_end    = Rb_size_t(unsafe.Sizeof(Rb_buf_end_t(0)))
)

func BytesToString(b []byte) string {
	return *(*string)(unsafe.Pointer(&b))
}

func Get_bool(buf []byte) bool {
	return buf[0] == 1
}

func Get_int8(buf []byte) (n int8) {
	n = int8(buf[0])
	return
}

func Get_uint8(buf []byte) (n uint8) {
	n = uint8(buf[0])
	return
}

func Get_int16(buf []byte) (n int16) {
	n |= int16(buf[0])
	n |= int16(buf[1]) << 8
	return
}

func Get_uint16(buf []byte) (n uint16) {
	n |= uint16(buf[0])
	n |= uint16(buf[1]) << 8
	return
}

func Get_int32(buf []byte) (n int32) {
	n |= int32(buf[0])
	n |= int32(buf[1]) << 8
	n |= int32(buf[2]) << 16
	n |= int32(buf[3]) << 24
	return
}

func Get_uint32(buf []byte) (n uint32) {
	n |= uint32(buf[0])
	n |= uint32(buf[1]) << 8
	n |= uint32(buf[2]) << 16
	n |= uint32(buf[3]) << 24
	return
}

func Get_int64(buf []byte) (n int64) {
	n |= int64(buf[0])
	n |= int64(buf[1]) << 8
	n |= int64(buf[2]) << 16
	n |= int64(buf[3]) << 24
	n |= int64(buf[4]) << 32
	n |= int64(buf[5]) << 40
	n |= int64(buf[6]) << 48
	n |= int64(buf[7]) << 56
	return
}

func Get_uint64(buf []byte) (n uint64) {
	n |= uint64(buf[0])
	n |= uint64(buf[1]) << 8
	n |= uint64(buf[2]) << 16
	n |= uint64(buf[3]) << 24
	n |= uint64(buf[4]) << 32
	n |= uint64(buf[5]) << 40
	n |= uint64(buf[6]) << 48
	n |= uint64(buf[7]) << 56
	return
}

func Get_float32(buf []byte) float32 {
	x := Get_uint32(buf)
	return math.Float32frombits(x)
}

func Get_float64(buf []byte) float64 {
	x := Get_uint64(buf)
	return math.Float64frombits(x)
}

func Set_bool(b bool, buf []byte) {
	buf[0] = 0
	if b {
		buf[0] = 1
	}
}

func Set_int8(n int8, buf []byte) {
	buf[0] = byte(n)
}

func Set_uint8(n uint8, buf []byte) {
	buf[0] = byte(n)
}

func Set_int16(n int16, buf []byte) {
	buf[0] = byte(n)
	buf[1] = byte(n >> 8)
}

func Set_uint16(n uint16, buf []byte) {
	buf[0] = byte(n)
	buf[1] = byte(n >> 8)
}

func Set_int32(n int32, buf []byte) {
	buf[0] = byte(n)
	buf[1] = byte(n >> 8)
	buf[2] = byte(n >> 16)
	buf[3] = byte(n >> 24)
}

func Set_uint32(n uint32, buf []byte) {
	buf[0] = byte(n)
	buf[1] = byte(n >> 8)
	buf[2] = byte(n >> 16)
	buf[3] = byte(n >> 24)
}

func Set_int64(n int64, buf []byte) {
	for i := uint(0); i < uint(Sizeof_int64); i++ {
		buf[i] = byte(n >> (i * 8))
	}
}

func Set_uint64(n uint64, buf []byte) {
	for i := uint(0); i < uint(Sizeof_uint64); i++ {
		buf[i] = byte(n >> (i * 8))
	}
}

func Set_float32(n float32, buf []byte) {
	Set_uint32(math.Float32bits(n), buf)
}

func Set_float64(n float64, buf []byte) {
	Set_uint64(math.Float64bits(n), buf)
}

func Get_rb_size(buf []byte) Rb_size_t {
	return Rb_size_t(Get_uint32(buf))
}

func Get_rb_field_size(buf []byte) Rb_field_size_t {
	return Rb_field_size_t(Get_uint8(buf))
}

func Get_rb_field_id(buf []byte) Rb_field_id_t {
	return Rb_field_id_t(Get_rb_field_size(buf))
}

func Get_rb_offset(buf []byte) Rb_offset_t {
	return Rb_offset_t(Get_rb_size(buf))
}

func Get_rb_buf_end(buf []byte) Rb_buf_end_t {
	return Rb_buf_end_t(Get_uint32(buf))
}

func Set_rb_size(n Rb_size_t, buf []byte) {
	Set_uint32(uint32(n), buf)
}

func Set_rb_field_size(n Rb_field_size_t, buf []byte) {
	Set_uint8(uint8(n), buf)
}

func Set_rb_field_id(n Rb_field_id_t, buf []byte) {
	Set_rb_field_size(Rb_field_size_t(n), buf)
}

func Set_rb_offset(n Rb_offset_t, buf []byte) {
	Set_rb_size(Rb_size_t(n), buf)
}

func Set_rb_buf_end(n Rb_buf_end_t, buf []byte) {
	Set_uint32(uint32(n), buf)
}

type Rb_buf_t struct {
	Size  Rb_size_t
	Start Rb_size_t
	Pos   Rb_size_t
	End   Rb_size_t
	Data  []byte
}

func Rb_get_buf_from_pos(buf *Rb_buf_t) []byte {
	return buf.Data[buf.Pos:]
}

func Rb_get_buf_from_offset(buf *Rb_buf_t, offset Rb_size_t) []byte {
	return buf.Data[offset:]
}

type Rb_field_table_head_t struct {
	Size   Rb_size_t
	Fields Rb_field_size_t
}

func rb_field_table_head_size() func() Rb_size_t {
	obj := Rb_field_table_head_t{0, 0}
	size := Rb_size_t(unsafe.Sizeof(obj.Size)) + Rb_size_t(unsafe.Sizeof(obj.Fields))
	return func() Rb_size_t {
		return size
	}
}

type Rb_field_table_item_t struct {
	Id     Rb_field_id_t
	Offset Rb_offset_t
}

func rb_field_table_item_size() func() Rb_size_t {
	obj := Rb_field_table_item_t{0, 0}
	size := Rb_size_t(unsafe.Sizeof(obj.Id)) + Rb_size_t(unsafe.Sizeof(obj.Offset))
	return func() Rb_size_t {
		return size
	}
}

var (
	Rb_field_table_head_size = rb_field_table_head_size()
	Rb_field_table_item_size = rb_field_table_item_size()
)

func create_buf(mm *mmap.MMap, size Rb_size_t) *Rb_buf_t {
	buf := Rb_buf_t{}
	buf.Start = 0
	buf.Size = size
	buf.Pos = buf.Start
	buf.End = buf.Start + buf.Size

	buf.Data = *mm

	return &buf
}

type Rb_dump_object_t func(obj_val interface{}, buf *Rb_buf_t) bool

func Rb_dump_buf(dump Rb_dump_object_t, obj_val interface{}, size Rb_size_t, path string) bool {
	f, err := os.Create(path)
	if nil != err {
		return false
	}

	defer f.Close()
	f.Seek(int64(size-1), os.SEEK_SET)
	data := []byte{0}
	f.Write(data)

	mm, err := mmap.Map(f, mmap.RDWR, 0)
	if nil != err {
		return false
	}
	defer mm.Unmap()

	buf := create_buf(&mm, size)
	rc := dump(obj_val, buf)

	mm.Flush()

	return rc
}

type Rb_load_object_t func(buf *Rb_buf_t, obj_val interface{}) bool

func Rb_load_buf(path string, load Rb_load_object_t, obj_val interface{}) bool {
	info, err := os.Stat(path)
	if nil != err {
		return false
	}
	f, err := os.Open(path)
	if nil != err {
		return false
	}
	defer f.Close()

	mm, err := mmap.Map(f, mmap.RDONLY, 0)
	if nil != err {
		return false
	}
	defer mm.Unmap()

	size := Get_rb_size(mm)

	if size < 1 || size > Rb_size_t(info.Size()) {
		return false
	}
	buf := create_buf(&mm, size)
	rc := load(buf, obj_val)
	return rc
}

func Rb_create_buf(size Rb_size_t) *Rb_buf_t {
	buf := Rb_buf_t{}
	buf.Size = size
	buf.Data = make([]byte, size)
	buf.Start = 0
	buf.Pos = buf.Start
	buf.End = buf.Start + buf.Size
	return &buf
}

func Rb_check_buf(buf *Rb_buf_t) bool {
	return buf.Size > 0 && buf.Start <= buf.Pos && buf.Pos <= buf.End && (buf.Start+buf.Size <= buf.End)
}

func Rb_nested_buf(buf *Rb_buf_t, offset Rb_offset_t) *Rb_buf_t {
	nested_buf := Rb_buf_t{}
	if Rb_check_buf(buf) {
		nested_buf.Data = buf.Data
		if 0 == offset {
			nested_buf.Start = buf.Pos
		} else {
			nested_buf.Start = buf.Start + Rb_size_t(offset)
		}
		nested_buf.End = buf.End
		nested_buf.Pos = nested_buf.Start
		nested_buf.Size = nested_buf.End - nested_buf.Start
	}
	return &nested_buf
}

func Rb_encode_check(buf *Rb_buf_t, size Rb_size_t) bool {
	return Rb_check_buf(buf) && (buf.Pos+size < buf.End)
}

func Rb_decode_check(buf *Rb_buf_t, offset Rb_offset_t, size Rb_size_t) bool {
	return Rb_check_buf(buf) && (buf.Start+Rb_size_t(offset)+size < buf.End) && (Rb_size_t(offset)+size < buf.Size)
}

func Rb_check_code(buf *Rb_buf_t, head *Rb_field_table_head_t) bool {
	if nil == head || !Rb_check_buf(buf) {
		return false
	}
	if buf.Start+head.Size > buf.End || head.Size > buf.Size {
		return false
	}
	size := Sizeof_rb_buf_end
	pos := buf.Start + (head.Size - size)
	end := Get_rb_buf_end(Rb_get_buf_from_offset(buf, pos))

	s := buf.Start
	e := buf.Start + Rb_seek_field_table_item(head.Fields)
	checkcode := Rb_buf_end_t(crc32.ChecksumIEEE(buf.Data[s:e]))
	if end != checkcode {
		return false
	}
	return true
}

func Rb_set_buf_size(size Rb_size_t, rb_val *Rb_buf_t) bool {
	if rb_val.Start+Sizeof_rb_size > rb_val.End {
		return false
	}
	Set_rb_size(size, Rb_get_buf_from_offset(rb_val, rb_val.Start))
	return true
}

func Rb_seek_field_table_item(index Rb_field_size_t) Rb_size_t {
	return Rb_field_table_head_size() + Rb_size_t(index)*Rb_field_table_item_size()
}

func Rb_set_field_count(fields Rb_field_size_t, rb_val *Rb_buf_t) bool {
	head_size := Rb_field_table_head_size()
	if rb_val.Start+head_size > rb_val.End {
		return false
	}
	offset := rb_val.Start + head_size - Sizeof_rb_field_size
	Set_rb_field_size(fields, Rb_get_buf_from_offset(rb_val, offset))
	rb_val.Pos = rb_val.Start + Rb_seek_field_table_item(fields)
	if rb_val.Pos > rb_val.End {
		return false
	}
	return true
}

func Rb_get_field_table_head(rb_val *Rb_buf_t) *Rb_field_table_head_t {
	head := Rb_field_table_head_t{0, 0}
	offset := rb_val.Start
	if (offset + Rb_field_table_head_size()) < rb_val.End {
		head.Size = Get_rb_size(Rb_get_buf_from_offset(rb_val, offset))
		head.Fields = Get_rb_field_size(Rb_get_buf_from_offset(rb_val, offset+Sizeof_rb_size))
	}
	return &head
}

func Rb_set_field_table_item(index Rb_field_size_t, id Rb_field_id_t, offset Rb_offset_t, rb_val *Rb_buf_t) bool {
	off := rb_val.Start + Rb_seek_field_table_item(index)
	size := Rb_field_table_item_size()
	if off+size > rb_val.End {
		return false
	}
	Set_rb_field_id(id, Rb_get_buf_from_offset(rb_val, off))
	Set_rb_offset(offset, Rb_get_buf_from_offset(rb_val, off+Sizeof_rb_field_id))
	return true
}

func Rb_get_field_table_item(index Rb_field_size_t, rb_val *Rb_buf_t, item *Rb_field_table_item_t) bool {
	off := rb_val.Start + Rb_seek_field_table_item(index)
	size := Rb_field_table_item_size()
	if nil == item || off+size > rb_val.End {
		return false
	}
	item.Id = Get_rb_field_id(Rb_get_buf_from_offset(rb_val, off))
	item.Offset = Get_rb_offset(Rb_get_buf_from_offset(rb_val, off+Sizeof_rb_field_id))
	return true
}

func Rb_encode_end(fields Rb_field_size_t, rb_val *Rb_buf_t) bool {
	size := Sizeof_rb_buf_end
	if !Rb_check_buf(rb_val) || rb_val.Pos+size > rb_val.End {
		return false
	}
	s := rb_val.Start
	e := rb_val.Start + Rb_seek_field_table_item(fields)
	end := crc32.ChecksumIEEE(rb_val.Data[s:e])
	Set_rb_buf_end(Rb_buf_end_t(end), Rb_get_buf_from_pos(rb_val))
	rb_val.Pos += size
	return true
}

func Rb_seek_array_table_item(index Rb_size_t) Rb_size_t {
	return Sizeof_rb_size + index*Sizeof_rb_offset
}

func Rb_set_array_count(size Rb_size_t, rb_val *Rb_buf_t) bool {
	if !Rb_check_buf(rb_val) {
		return false
	}
	if rb_val.Pos+Sizeof_rb_size > rb_val.End {
		return false
	}
	Set_rb_size(size, Rb_get_buf_from_pos(rb_val))
	rb_val.Pos = rb_val.Start + Rb_seek_array_table_item(size)
	if rb_val.Pos > rb_val.End {
		return false
	}
	return true
}

func Rb_get_array_count(rb_val *Rb_buf_t) Rb_size_t {
	off := rb_val.Start
	if off+Sizeof_rb_size < rb_val.End {
		return Get_rb_size(Rb_get_buf_from_offset(rb_val, off))
	}
	return 0
}

func Rb_set_array_table_item(index Rb_size_t, offset Rb_offset_t, rb_val *Rb_buf_t) bool {
	off := rb_val.Start + Rb_seek_array_table_item(index)
	if off+Sizeof_rb_offset > rb_val.End {
		return false
	}
	Set_rb_offset(offset, Rb_get_buf_from_offset(rb_val, off))
	return true
}

func Rb_get_array_table_item(index Rb_size_t, rb_val *Rb_buf_t) (bool, Rb_offset_t) {
	off := rb_val.Start + Rb_seek_array_table_item(index)
	if off+Sizeof_rb_offset > rb_val.End {
		return false, 0
	}
	return true, Get_rb_offset(Rb_get_buf_from_offset(rb_val, off))
}

func Rb_init_string(obj_val *string) {
	if nil != obj_val {
		*obj_val = ""
	}
}

func Rb_set_string(src *string, dst *string) bool {
	if nil == src || nil == dst {
		return false
	}
	*dst = *src
	return true
}

func Rb_eq_string(src *string, dst *string) bool {
	if nil == src || nil == dst {
		return false
	}
	return *src == *dst
}

func Rb_sizeof_string(obj_val *string) Rb_size_t {
	return Sizeof_rb_size + Rb_size_t(len(*obj_val))
}

func Rb_encode_string(obj_val *string, rb_val *Rb_buf_t) bool {
	if nil == obj_val {
		return false
	}
	size := Rb_sizeof_string(obj_val)
	if !Rb_encode_check(rb_val, size) {
		return false
	}
	size = Rb_size_t(len(*obj_val))
	Set_rb_size(size, Rb_get_buf_from_pos(rb_val))
	rb_val.Pos += Sizeof_rb_size
	if size > 0 {
		copy(Rb_get_buf_from_pos(rb_val), *obj_val)
		rb_val.Pos += size
	}
	return true
}

func Rb_decode_string(rb_val *Rb_buf_t, offset Rb_offset_t, obj_val *string) bool {
	if nil == obj_val {
		return false
	}
	if !Rb_decode_check(rb_val, offset, Sizeof_rb_size) {
		return false
	}
	size := Get_rb_size(Rb_get_buf_from_offset(rb_val, rb_val.Start+Rb_size_t(offset)))
	if size > 0 {
		offset += Rb_offset_t(Sizeof_rb_size)
		if !Rb_decode_check(rb_val, offset, size) {
			return false
		}
		s := rb_val.Start + Rb_size_t(offset)
		e := s + size
		*obj_val = string(rb_val.Data[s:e])
	} else {
		*obj_val = ""
	}
	return true
}
