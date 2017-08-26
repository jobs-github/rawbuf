#ifndef __rawbuf_20160227172332_h__
#define __rawbuf_20160227172332_h__

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
#include <string>
#include <vector>
#include <map>

namespace rawbuf {

typedef uint32_t rb_size_t;
typedef uint8_t rb_field_size_t;
typedef rb_field_size_t rb_field_id_t;
typedef rb_size_t rb_offset_t;
typedef uint32_t rb_buf_end_t;

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

rb_buf_t rb_create_buf(rb_size_t size);
rb_buf_t rb_create_buf(void * addr, rb_size_t size);
void rb_dispose_buf(rb_buf_t& buf);
rb_buf_t rb_nested_buf(const rb_buf_t& buf, rb_offset_t offset);

bool rb_check_code(const rb_buf_t& buf, const rb_field_table_head_t& head);

bool rb_set_buf_size(rb_size_t size, rb_buf_t& rb_val);
rb_size_t rb_seek_field_table_item(rb_field_size_t index);
bool rb_set_field_count(rb_field_size_t fields, rb_buf_t& rb_val);
rb_field_table_head_t rb_get_field_table_head(const rb_buf_t& rb_val);
bool rb_set_field_table_item(rb_field_size_t index, rb_field_id_t id, rb_offset_t offset, rb_buf_t& rb_val);
bool rb_get_field_table_item(rb_field_size_t index, const rb_buf_t& rb_val, rb_field_table_item_t& item);
bool rb_encode_end(rb_field_size_t fields, rb_buf_t& rb_val);

bool rb_set_array_count(rb_size_t size, rb_buf_t& rb_val);
rb_size_t rb_get_array_count(const rb_buf_t& rb_val);
bool rb_set_array_table_item(rb_size_t index, rb_offset_t offset, rb_buf_t& rb_val);
bool rb_get_array_table_item(rb_size_t index, rb_buf_t& rb_val, rb_offset_t& item);

rb_size_t rb_sizeof(const bool& obj_val);
rb_size_t rb_sizeof(const int8_t& obj_val);
rb_size_t rb_sizeof(const uint8_t& obj_val);
rb_size_t rb_sizeof(const int16_t& obj_val);
rb_size_t rb_sizeof(const uint16_t& obj_val);
rb_size_t rb_sizeof(const int32_t& obj_val);
rb_size_t rb_sizeof(const uint32_t& obj_val);
rb_size_t rb_sizeof(const int64_t& obj_val);
rb_size_t rb_sizeof(const uint64_t& obj_val);
rb_size_t rb_sizeof(const float& obj_val);
rb_size_t rb_sizeof(const double& obj_val);

bool rb_encode(const bool& obj_val, rb_buf_t& rb_val);
bool rb_encode(const int8_t& obj_val, rb_buf_t& rb_val);
bool rb_encode(const uint8_t& obj_val, rb_buf_t& rb_val);
bool rb_encode(const int16_t& obj_val, rb_buf_t& rb_val);
bool rb_encode(const uint16_t& obj_val, rb_buf_t& rb_val);
bool rb_encode(const int32_t& obj_val, rb_buf_t& rb_val);
bool rb_encode(const uint32_t& obj_val, rb_buf_t& rb_val);
bool rb_encode(const int64_t& obj_val, rb_buf_t& rb_val);
bool rb_encode(const uint64_t& obj_val, rb_buf_t& rb_val);
bool rb_encode(const float& obj_val, rb_buf_t& rb_val);
bool rb_encode(const double& obj_val, rb_buf_t& rb_val);

bool rb_decode(const rb_buf_t& rb_val, rb_offset_t offset, bool& obj_val);
bool rb_decode(const rb_buf_t& rb_val, rb_offset_t offset, int8_t& obj_val);
bool rb_decode(const rb_buf_t& rb_val, rb_offset_t offset, uint8_t& obj_val);
bool rb_decode(const rb_buf_t& rb_val, rb_offset_t offset, int16_t& obj_val);
bool rb_decode(const rb_buf_t& rb_val, rb_offset_t offset, uint16_t& obj_val);
bool rb_decode(const rb_buf_t& rb_val, rb_offset_t offset, int32_t& obj_val);
bool rb_decode(const rb_buf_t& rb_val, rb_offset_t offset, uint32_t& obj_val);
bool rb_decode(const rb_buf_t& rb_val, rb_offset_t offset, int64_t& obj_val);
bool rb_decode(const rb_buf_t& rb_val, rb_offset_t offset, uint64_t& obj_val);
bool rb_decode(const rb_buf_t& rb_val, rb_offset_t offset, float& obj_val);
bool rb_decode(const rb_buf_t& rb_val, rb_offset_t offset, double& obj_val);

rb_size_t rb_sizeof(const std::string& obj_val);
bool rb_encode(const std::string& obj_val, rb_buf_t& rb_val);
bool rb_decode(const rb_buf_t& rb_val, rb_offset_t offset, std::string& obj_val);

template <typename T>
rb_size_t rb_sizeof(const std::vector<T>& obj_val);
template <typename T>
bool rb_encode(const std::vector<T>& obj_val, rb_buf_t& rb_val);
template <typename T>
bool rb_decode(const rb_buf_t& rb_val, rb_offset_t offset, std::vector<T>& obj_val);

template <typename T>
rb_size_t rb_sizeof(const std::map<std::string, T>& obj_val);
template <typename T>
bool rb_encode(const std::map<std::string, T>& obj_val, rb_buf_t& rb_val);
template <typename T>
bool rb_decode(const rb_buf_t& rb_val, rb_offset_t offset, std::map<std::string, T>& obj_val);

template <typename T>
bool rb_encode_field(rb_field_size_t index, rb_field_id_t id, const T& field, rb_buf_t& buf);
template <typename T>
bool rb_decode_field(
    rb_field_id_t field_id,
    const rb_field_table_item_t& item,
    const rb_buf_t& rb_val,
    bool& rc,
    bool& rb_has_field,
    T& field);

template <typename T>
bool rb_encode_base(rb_field_size_t fields, const T& obj_val, rb_buf_t& rb_val);
template <typename T>
bool rb_decode_base(const rb_buf_t& rb_val, rb_offset_t offset, T& obj_val);

template <typename T>
bool rb_dump_base(const T& obj_val, const char * path);
template <typename T>
bool rb_load_base(const char * path, T& obj_val);

template <typename T>
rb_size_t rb_sizeof(const std::vector<T>& obj_val)
{
    rb_size_t array_count = obj_val.size();
    rb_size_t size = sizeof(rb_size_t) + array_count * sizeof(rb_size_t);
    for (rb_size_t i = 0; i < array_count; ++i)
    {
        size += rb_sizeof(obj_val[i]);
    }
    return size;
}

template <typename T>
bool rb_encode(const std::vector<T>& obj_val, rb_buf_t& rb_val)
{
    rb_buf_t buf = rb_nested_buf(rb_val, 0);
    if (buf.size < 1)
    {
        return false;
    }
    rb_size_t array_count = obj_val.size();
    if (!rb_set_array_count(array_count, buf))
    {
        return false;
    }
    for (rb_size_t i = 0; i < array_count; ++i)
    {
        if (!rb_set_array_table_item(i, buf.pos - buf.start, buf))
        {
            return false;
        }
        if (!rb_encode(obj_val[i], buf))
        {
            return false;
        }
    }
    rb_val.pos = buf.pos;
    return true;
}

template <typename T>
bool rb_decode(const rb_buf_t& rb_val, rb_offset_t offset, std::vector<T>& obj_val)
{
    rb_buf_t buf = rb_nested_buf(rb_val, offset);
    if (buf.size < 1)
    {
        return false;
    }
    rb_size_t size = rb_get_array_count(buf);
    if (size < 1)
    {
        return true;
    }

    rb_offset_t off = 0;
    obj_val.reserve(size);
    for (rb_size_t i = 0; i < size; ++i)
    {
        if (!rb_get_array_table_item(i, buf, off))
        {
            return false;
        }
        T tmp_obj_val;
        if (!rb_decode(buf, off, tmp_obj_val))
        {
            return false;
        }
        obj_val.push_back(tmp_obj_val);
    }
    return true;
}

template <typename T>
rb_size_t rb_sizeof(const std::map<std::string, T>& obj_val)
{
    rb_size_t array_count = obj_val.size();
    rb_size_t size = sizeof(rb_size_t) + array_count * sizeof(rb_size_t);
    for (typename std::map<std::string, T>::const_iterator it = obj_val.begin(); it != obj_val.end(); ++it)
    {
        size += rb_sizeof(it->first);
        size += rb_sizeof(it->second);
    }
    return size;
}
template <typename T>
bool rb_encode(const std::map<std::string, T>& obj_val, rb_buf_t& rb_val)
{
    rb_buf_t buf = rb_nested_buf(rb_val, 0);
    if (buf.size < 1)
    {
        return false;
    }
    rb_size_t array_count = obj_val.size();
    if (!rb_set_array_count(array_count, buf))
    {
        return false;
    }
    rb_size_t i = 0;
    for (typename std::map<std::string, T>::const_iterator it = obj_val.begin(); it != obj_val.end(); ++it, ++i)
    {
        if (!rb_set_array_table_item(i, buf.pos - buf.start, buf))
        {
            return false;
        }
        if (!rb_encode(it->first, buf))
        {
            return false;
        }
        if (!rb_encode(it->second, buf))
        {
            return false;
        }
    }
    rb_val.pos = buf.pos;
    return true;
}

template <typename T>
bool rb_decode(const rb_buf_t& rb_val, rb_offset_t offset, std::map<std::string, T>& obj_val)
{
    rb_buf_t buf = rb_nested_buf(rb_val, offset);
    if (buf.size < 1)
    {
        return false;
    }
    rb_size_t size = rb_get_array_count(buf);
    if (size < 1)
    {
        return true;
    }

    std::string key;
    rb_offset_t off = 0;
    for (rb_size_t i = 0; i < size; ++i)
    {
        if (!rb_get_array_table_item(i, buf, off))
        {
            return false;
        }
        if (!rb_decode(buf, off, key))
        {
            return false;
        }
        T val;
        if (!rb_decode(buf, off + rb_sizeof(key), val))
        {
            return false;
        }
        obj_val[key] = val;
    }
    return true;
}

template <typename T>
bool rb_encode_field(rb_field_size_t index, rb_field_id_t id, const T& field, rb_buf_t& buf)
{
    if (!rb_set_field_table_item(index, id, buf.pos - buf.start, buf))
    {
        return false;
    }
    if (!rb_encode(field, buf))
    {
        return false;
    }
    return true;
}

template <typename T>
bool rb_decode_field(
    rb_field_id_t field_id,
    const rb_field_table_item_t& item,
    const rb_buf_t& rb_val,
    bool& rc,
    bool& rb_has_field,
    T& field)
{
    if (item.id == field_id)
    {
        rc = rb_decode(rb_val, item.offset, field);
        if (rc)
        {
            rb_has_field = true;
        }
        return true;
    }
    return false;
}

template <typename T>
bool rb_encode_base(const T& obj_val, rb_buf_t& rb_val)
{
    rb_buf_t buf = rb_nested_buf(rb_val, 0);
    if (buf.size < 1)
    {
        return false;
    }
    do
    {
        rb_field_size_t fields = obj_val.rb_fields();
        if (!rb_set_field_count(fields, buf)) break;
        if (!obj_val.encode(buf)) break;
        if (!rb_set_buf_size(buf.pos - buf.start + sizeof(rb_buf_end_t), buf)) break;
        if (!rb_encode_end(fields, buf)) break;
        rb_val.pos = buf.pos;

        return true;
    } while (0);

    return false;
}

template <typename T>
bool rb_decode_base(const rb_buf_t& rb_val, rb_offset_t offset, T& obj_val)
{
    rb_buf_t buf = rb_nested_buf(rb_val, offset);
    if (buf.size < 1)
    {
        return false;
    }
    rb_field_table_head_t head = rb_get_field_table_head(buf);
    if (head.fields < 1 || !rb_check_code(buf, head))
    {
        return false;
    }
    rb_field_table_item_t item = { 0, 0 };
    for (rb_field_size_t i = 0; i < head.fields; ++i)
    {
        if (!rb_get_field_table_item(i, buf, item))
        {
            return false;
        }
        if (item.offset >= head.size)
        {
            return false;
        }
        if (item.offset > 0 && !obj_val.decode(item, buf))
        {
            return false;
        }
    }
    return true;
}

struct rb_wbuf_t
{
    rb_wbuf_t(const char * path, size_t size);
    ~rb_wbuf_t();
    void * data() { return addr_; }
private:
    
#ifdef WIN32
    void * fd_;
    void * file_map_;
#else
    int fd_;
#endif
    void * addr_;
    size_t size_;
};

template <typename T>
bool rb_dump_base(const T& obj_val, const char * path)
{
    rb_size_t size = rb_sizeof(obj_val);
    if (size < 1)
    {
        return false;
    }
    rb_wbuf_t wbuf(path, size);
    void * addr = wbuf.data();
    if (!addr)
    {
        return false;
    }
    rb_buf_t buf = rb_create_buf(addr, size);
    return rb_encode(obj_val, buf);
}

struct rb_rbuf_t
{
    rb_rbuf_t(const char * path);
    ~rb_rbuf_t();
    void * data() { return addr_; }
    bool check(rb_size_t size);
private:

#ifdef WIN32
    void * fd_;
    void * file_map_;
#else
    int fd_;
#endif
    void * addr_;
    size_t size_;
};

void rb_read_size(const void * addr, rb_size_t& size);

template <typename T>
bool rb_load_base(const char * path, T& obj_val)
{
    if (!path)
    {
        return false;
    }
    rb_rbuf_t rbuf(path);
    void * addr = rbuf.data();
    if (!addr)
    {
        return false;
    }
    rb_size_t size = 0;
    rb_read_size(addr, size);
    if (!rbuf.check(size))
    {
        return false;
    }
    rb_buf_t buf = rb_create_buf(addr, size);
    return rb_decode(buf, 0, obj_val);
}

} // namespace rawbuf

#endif // __rawbuf_20160227172332_h__
