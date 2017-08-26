#ifndef __rawbuf_utils_20160218103516_h__
#define __rawbuf_utils_20160218103516_h__

#ifdef WIN32
    #pragma warning(disable: 4244)
    #pragma warning(disable: 4305)
    #pragma warning(disable: 4996)
#endif // WIN32

#include <stdint.h>
#include <limits.h>
#include <float.h>
#include <string.h>
#include <stdlib.h>

void little_endian_copy(void * dst, const void * src, size_t size);

#define rb_make_str(s) { sizeof(s) - 1, (char *) s }

typedef uint8_t rb_bool_t;
typedef uint32_t rb_size_t;
typedef uint8_t rb_field_size_t;
typedef rb_field_size_t rb_field_id_t;
typedef rb_size_t rb_offset_t;
typedef uint32_t rb_buf_end_t;

typedef struct
{
    rb_size_t len;
    char * data;
} rb_str_t;

typedef struct
{
    rb_size_t size;
    uint8_t * start;
    uint8_t * pos;
    uint8_t * end;
} rb_buf_t;

#pragma pack(push)
#pragma pack(1)
typedef struct
{
    rb_size_t size;
    rb_field_size_t fields;
} rb_field_table_head_t;
typedef struct
{
    rb_field_id_t id;
    rb_offset_t offset;
} rb_field_table_item_t;
#pragma pack(pop)

typedef struct
{
      void *(*malloc_fn)(size_t size);
      void (*free_fn)(void * obj);
} rb_hooks_t;

void rb_init_hooks(rb_hooks_t* hooks);
void * rb_malloc(size_t size);
void rb_free(void * obj);

typedef rb_bool_t (*rb_dump_object_t)(const void * obj_val, rb_buf_t * buf);
rb_bool_t rb_dump_buf(rb_dump_object_t dump, const void * obj_val, rb_size_t size, const char * path);
typedef rb_bool_t (*rb_load_object_t)(const rb_buf_t * buf, void * obj_val);
rb_bool_t rb_load_buf(const char * path, rb_load_object_t load, void * obj_val);

uint32_t rb_crc32_long(void * p, rb_size_t size);
rb_str_t rb_create_string(const char * str);
rb_bool_t rb_copy_to_string(const rb_str_t * src, rb_str_t * dst);

rb_buf_t rb_create_buf(rb_size_t size);
void rb_dispose_buf(rb_buf_t * buf);
rb_buf_t rb_nested_buf(const rb_buf_t * buf, rb_offset_t offset);

rb_bool_t rb_check_buf(const rb_buf_t * buf);
rb_bool_t rb_encode_check(const rb_buf_t * buf, rb_size_t size);
rb_bool_t rb_decode_check(const rb_buf_t * buf, rb_offset_t offset, rb_size_t size);
rb_bool_t rb_check_code(const rb_buf_t * rb_val, const rb_field_table_head_t * head);

rb_bool_t rb_set_buf_size(rb_size_t size, rb_buf_t * rb_val);
rb_size_t rb_seek_field_table_item(rb_field_size_t index);
rb_bool_t rb_set_field_count(rb_field_size_t fields, rb_buf_t * rb_val);
rb_field_table_head_t rb_get_field_table_head(const rb_buf_t * rb_val);
rb_bool_t rb_set_field_table_item(rb_field_size_t index, rb_field_id_t id, rb_offset_t offset, rb_buf_t * rb_val);
rb_bool_t rb_get_field_table_item(rb_field_size_t index, const rb_buf_t * rb_val, rb_field_table_item_t * item);
rb_bool_t rb_encode_end(rb_field_size_t fields, rb_buf_t * rb_val);

rb_size_t rb_seek_array_table_item(rb_size_t index);
rb_bool_t rb_set_array_count(rb_size_t size, rb_buf_t * rb_val);
rb_size_t rb_get_array_count(const rb_buf_t * rb_val);
rb_bool_t rb_set_array_table_item(rb_size_t index, rb_offset_t offset, rb_buf_t * rb_val);
rb_bool_t rb_get_array_table_item(rb_size_t index, rb_buf_t * rb_val, rb_offset_t * item);

void rb_init_string(rb_str_t * obj_val);
rb_bool_t rb_set_string(const rb_str_t * src, rb_str_t * dst);
rb_bool_t rb_eq_string(const rb_str_t * src, const rb_str_t * dst);
void rb_dispose_string(rb_str_t * obj_val);
rb_size_t rb_sizeof_string(const rb_str_t * obj_val);
rb_bool_t rb_encode_string(const rb_str_t * obj_val, rb_buf_t * rb_val);
rb_bool_t rb_decode_string(const rb_buf_t * rb_val, rb_offset_t offset, rb_str_t * obj_val);

#endif // __rawbuf_utils_20160218103516_h__
