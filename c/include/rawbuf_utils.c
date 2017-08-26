#include "rawbuf_utils.h"
#include <math.h>
#include <assert.h>

#ifdef WIN32
    #include <Windows.h>
    #include <stdio.h>
#else
    #include <stdbool.h>
    #include <unistd.h>
    #include <sys/mman.h>
    #include <sys/stat.h>
    #include <fcntl.h>
#endif

#if !defined(IS_LITTLE_ENDIAN)
    #if defined(__GNUC__) || defined(__clang__)
        #ifdef __BIG_ENDIAN__
            #define IS_LITTLE_ENDIAN 0
        #else
            #define IS_LITTLE_ENDIAN 1
    #endif // __BIG_ENDIAN__
    #elif defined(_MSC_VER)
        #if defined(_M_PPC)
            #define IS_LITTLE_ENDIAN 0
        #else
            #define IS_LITTLE_ENDIAN 1
        #endif
    #else
        #error Unable to determine endianness, define IS_LITTLE_ENDIAN.
    #endif
#endif // !defined(IS_LITTLE_ENDIAN)

static uint32_t  rb_crc32_table256[] = {
    0x00000000, 0x77073096, 0xee0e612c, 0x990951ba,
    0x076dc419, 0x706af48f, 0xe963a535, 0x9e6495a3,
    0x0edb8832, 0x79dcb8a4, 0xe0d5e91e, 0x97d2d988,
    0x09b64c2b, 0x7eb17cbd, 0xe7b82d07, 0x90bf1d91,
    0x1db71064, 0x6ab020f2, 0xf3b97148, 0x84be41de,
    0x1adad47d, 0x6ddde4eb, 0xf4d4b551, 0x83d385c7,
    0x136c9856, 0x646ba8c0, 0xfd62f97a, 0x8a65c9ec,
    0x14015c4f, 0x63066cd9, 0xfa0f3d63, 0x8d080df5,
    0x3b6e20c8, 0x4c69105e, 0xd56041e4, 0xa2677172,
    0x3c03e4d1, 0x4b04d447, 0xd20d85fd, 0xa50ab56b,
    0x35b5a8fa, 0x42b2986c, 0xdbbbc9d6, 0xacbcf940,
    0x32d86ce3, 0x45df5c75, 0xdcd60dcf, 0xabd13d59,
    0x26d930ac, 0x51de003a, 0xc8d75180, 0xbfd06116,
    0x21b4f4b5, 0x56b3c423, 0xcfba9599, 0xb8bda50f,
    0x2802b89e, 0x5f058808, 0xc60cd9b2, 0xb10be924,
    0x2f6f7c87, 0x58684c11, 0xc1611dab, 0xb6662d3d,
    0x76dc4190, 0x01db7106, 0x98d220bc, 0xefd5102a,
    0x71b18589, 0x06b6b51f, 0x9fbfe4a5, 0xe8b8d433,
    0x7807c9a2, 0x0f00f934, 0x9609a88e, 0xe10e9818,
    0x7f6a0dbb, 0x086d3d2d, 0x91646c97, 0xe6635c01,
    0x6b6b51f4, 0x1c6c6162, 0x856530d8, 0xf262004e,
    0x6c0695ed, 0x1b01a57b, 0x8208f4c1, 0xf50fc457,
    0x65b0d9c6, 0x12b7e950, 0x8bbeb8ea, 0xfcb9887c,
    0x62dd1ddf, 0x15da2d49, 0x8cd37cf3, 0xfbd44c65,
    0x4db26158, 0x3ab551ce, 0xa3bc0074, 0xd4bb30e2,
    0x4adfa541, 0x3dd895d7, 0xa4d1c46d, 0xd3d6f4fb,
    0x4369e96a, 0x346ed9fc, 0xad678846, 0xda60b8d0,
    0x44042d73, 0x33031de5, 0xaa0a4c5f, 0xdd0d7cc9,
    0x5005713c, 0x270241aa, 0xbe0b1010, 0xc90c2086,
    0x5768b525, 0x206f85b3, 0xb966d409, 0xce61e49f,
    0x5edef90e, 0x29d9c998, 0xb0d09822, 0xc7d7a8b4,
    0x59b33d17, 0x2eb40d81, 0xb7bd5c3b, 0xc0ba6cad,
    0xedb88320, 0x9abfb3b6, 0x03b6e20c, 0x74b1d29a,
    0xead54739, 0x9dd277af, 0x04db2615, 0x73dc1683,
    0xe3630b12, 0x94643b84, 0x0d6d6a3e, 0x7a6a5aa8,
    0xe40ecf0b, 0x9309ff9d, 0x0a00ae27, 0x7d079eb1,
    0xf00f9344, 0x8708a3d2, 0x1e01f268, 0x6906c2fe,
    0xf762575d, 0x806567cb, 0x196c3671, 0x6e6b06e7,
    0xfed41b76, 0x89d32be0, 0x10da7a5a, 0x67dd4acc,
    0xf9b9df6f, 0x8ebeeff9, 0x17b7be43, 0x60b08ed5,
    0xd6d6a3e8, 0xa1d1937e, 0x38d8c2c4, 0x4fdff252,
    0xd1bb67f1, 0xa6bc5767, 0x3fb506dd, 0x48b2364b,
    0xd80d2bda, 0xaf0a1b4c, 0x36034af6, 0x41047a60,
    0xdf60efc3, 0xa867df55, 0x316e8eef, 0x4669be79,
    0xcb61b38c, 0xbc66831a, 0x256fd2a0, 0x5268e236,
    0xcc0c7795, 0xbb0b4703, 0x220216b9, 0x5505262f,
    0xc5ba3bbe, 0xb2bd0b28, 0x2bb45a92, 0x5cb36a04,
    0xc2d7ffa7, 0xb5d0cf31, 0x2cd99e8b, 0x5bdeae1d,
    0x9b64c2b0, 0xec63f226, 0x756aa39c, 0x026d930a,
    0x9c0906a9, 0xeb0e363f, 0x72076785, 0x05005713,
    0x95bf4a82, 0xe2b87a14, 0x7bb12bae, 0x0cb61b38,
    0x92d28e9b, 0xe5d5be0d, 0x7cdcefb7, 0x0bdbdf21,
    0x86d3d2d4, 0xf1d4e242, 0x68ddb3f8, 0x1fda836e,
    0x81be16cd, 0xf6b9265b, 0x6fb077e1, 0x18b74777,
    0x88085ae6, 0xff0f6a70, 0x66063bca, 0x11010b5c,
    0x8f659eff, 0xf862ae69, 0x616bffd3, 0x166ccf45,
    0xa00ae278, 0xd70dd2ee, 0x4e048354, 0x3903b3c2,
    0xa7672661, 0xd06016f7, 0x4969474d, 0x3e6e77db,
    0xaed16a4a, 0xd9d65adc, 0x40df0b66, 0x37d83bf0,
    0xa9bcae53, 0xdebb9ec5, 0x47b2cf7f, 0x30b5ffe9,
    0xbdbdf21c, 0xcabac28a, 0x53b39330, 0x24b4a3a6,
    0xbad03605, 0xcdd70693, 0x54de5729, 0x23d967bf,
    0xb3667a2e, 0xc4614ab8, 0x5d681b02, 0x2a6f2b94,
    0xb40bbe37, 0xc30c8ea1, 0x5a05df1b, 0x2d02ef8d
};

void little_endian_copy(void * dst, const void * src, size_t size)
{
#if IS_LITTLE_ENDIAN
    memcpy(dst, src, size);
#else
    #if defined(_MSC_VER)
        #define BYTE_SWAP16 _byteswap_ushort
        #define BYTE_SWAP32 _byteswap_ulong
        #define BYTE_SWAP64 _byteswap_uint64
    #else
        #if defined(__GNUC__) && __GNUC__ * 100 + __GNUC_MINOR__ < 408
            // __builtin_bswap16 was missing prior to GCC 4.8.
            #define BYTE_SWAP16(x) \
                static_cast<uint16_t>(__builtin_bswap32(static_cast<uint32_t>(x) << 16))
        #else
            #define BYTE_SWAP16 __builtin_bswap16
        #endif
        #define BYTE_SWAP32 __builtin_bswap32
        #define BYTE_SWAP64 __builtin_bswap64
    #endif
    if (size == 1)
    {
        memcpy(dst, src, size);
    }
    else if (size == 2)
    {
        uint16_t tmp = BYTE_SWAP16(*(uint16_t *)(src));
        memcpy(dst, &tmp, size);
    }
    else if (size == 4)
    {
        uint32_t tmp = BYTE_SWAP32(*(uint32_t *)(src));
        memcpy(dst, &tmp, size);
    }
    else if (size == 8)
    {
        uint64_t tmp = BYTE_SWAP64(*(uint64_t *)(src));
        memcpy(dst, &tmp, size);
    }
    else
    {
        assert(0);
    }
#endif
}

static void *(*g_rb_malloc)(size_t size) = malloc;
static void (*g_rb_free)(void *ptr) = free;

void rb_init_hooks(rb_hooks_t* hooks)
{
    if (!hooks)
    {
        g_rb_malloc = malloc;
        g_rb_free = free;
        return;
    }

    g_rb_malloc = (hooks->malloc_fn) ? hooks->malloc_fn : malloc;
    g_rb_free = (hooks->free_fn) ? hooks->free_fn : free;
}

void * rb_malloc(size_t size)
{
    return g_rb_malloc(size);
}

void rb_free(void * obj)
{
    return g_rb_free(obj);
}

rb_buf_t __create_buf(void * addr, rb_size_t size)
{
    rb_buf_t buf;
    buf.start = (uint8_t *) addr;
    buf.size = size;
    buf.pos = buf.start;
    buf.end = buf.start + buf.size;
    return buf;
}
#ifdef WIN32

rb_bool_t rb_dump_buf(rb_dump_object_t dump, const void * obj_val, rb_size_t size, const char * path)
{
    FILE * fp = fopen(path, "w");
    if (!fp)
    {
        return false;
    }
    _fseeki64(fp, size - 1, SEEK_SET);
    fputc(0, fp);
    fclose(fp);

    rb_bool_t rc = true;
    HANDLE fd = INVALID_HANDLE_VALUE;
    HANDLE file_map = INVALID_HANDLE_VALUE;
    void * addr = NULL;
    do
    {
        fd = CreateFileA(path, GENERIC_WRITE|GENERIC_READ, FILE_SHARE_WRITE, NULL, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
        if (INVALID_HANDLE_VALUE == fd)
        {
            rc = false;
            break;
        }
        LARGE_INTEGER file_size;
        file_size.QuadPart = size;

        file_map = CreateFileMappingA(fd, NULL, PAGE_READWRITE, (DWORD)(file_size.HighPart), (DWORD)(file_size.LowPart), NULL);
        if (INVALID_HANDLE_VALUE == file_map)
        {
            rc = false;
            break;
        }
        addr = MapViewOfFile(file_map, FILE_MAP_WRITE, 0, 0, size);
        if (!addr)
        {
            rc = false;
            break;
        }
        rb_buf_t buf = __create_buf(addr, size);
        rc = dump(obj_val, &buf);
    } while (0);

    if (NULL != addr)
    {
        UnmapViewOfFile(addr);
    }
    if (INVALID_HANDLE_VALUE != file_map)
    {
        CloseHandle(file_map);
    }
    if (INVALID_HANDLE_VALUE != fd)
    {
        CloseHandle(fd);
    }
    return rc;
}

rb_bool_t rb_load_buf(const char * path, rb_load_object_t load, void * obj_val)
{
    if (!path || !load || !obj_val)
    {
        return false;
    }
    rb_bool_t rc = true;
    HANDLE fd = INVALID_HANDLE_VALUE;
    HANDLE file_map = INVALID_HANDLE_VALUE;
    void * addr = NULL;
    do
    {
        fd = CreateFileA(path, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
        if (INVALID_HANDLE_VALUE == fd)
        {
            rc = false;
            break;
        }

        DWORD low, high;
        low = GetFileSize(fd, &high);
        LARGE_INTEGER file_size;
        file_size.LowPart = low;
        file_size.HighPart = high;

        file_map = CreateFileMappingA(fd, NULL, PAGE_READONLY, (DWORD)(file_size.HighPart), (DWORD)(file_size.LowPart), NULL);
        if (INVALID_HANDLE_VALUE == file_map)
        {
            rc = false;
            break;
        }

        addr = MapViewOfFile(file_map, FILE_MAP_READ, 0, 0, file_size.QuadPart);
        if (NULL == addr)
        {
            rc = false;
            break;
        }

        rb_size_t size = 0;
        memcpy(&size, addr, sizeof(rb_size_t));
        if (size < 1 || size > (rb_size_t) file_size.QuadPart)
        {
            rc = false;
            break;
        }

        rb_buf_t buf = __create_buf(addr, size);
        rc = load(&buf, obj_val);

    } while (0);

    if (NULL != addr)
    {
        UnmapViewOfFile(addr);
    }
    if (INVALID_HANDLE_VALUE != file_map)
    {
        CloseHandle(file_map);
    }
    if (INVALID_HANDLE_VALUE != fd)
    {
        CloseHandle(fd);
    }
    return rc;
}

#else

rb_bool_t rb_dump_buf(rb_dump_object_t dump, const void * obj_val, rb_size_t size, const char * path)
{
    rb_bool_t rc = true;
    int fd = -1;
    void * addr = MAP_FAILED;
    do
    {
        fd = open(path, O_CREAT|O_RDWR|O_TRUNC);
        if (-1 == fd)
        {
            rc = false;
            break;
        }
        lseek(fd, size - 1, SEEK_SET);
        write(fd, "", 1);

        addr = mmap(NULL, size, PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0);
        if (MAP_FAILED == addr)
        {
            rc = false;
            break;
        }
        rb_buf_t buf = __create_buf(addr, size);
        rc = dump(obj_val, &buf);
    } while (0);

    if (MAP_FAILED != addr)
    {
        munmap(addr, size);
    }
    if (-1 != fd)
    {
        close(fd);
    }
    return rc;
}

rb_bool_t rb_load_buf(const char * path, rb_load_object_t load, void * obj_val)
{
    if (!path || !load || !obj_val)
    {
        return false;
    }
    struct stat st;
    if (lstat(path, &st) < 0)
    {
        return false;
    }
    rb_bool_t rc = true;
    int fd = -1;
    void * addr = MAP_FAILED;
    do
    {
        fd = open(path, O_RDONLY);
        if (-1 == fd)
        {
            rc = false;
            break;
        }

        addr = mmap(NULL, st.st_size, PROT_READ, MAP_SHARED, fd, 0);
        if (MAP_FAILED == addr)
        {
            rc = false;
            break;
        }

        rb_size_t size = 0;
        little_endian_copy(&size, addr, sizeof(rb_size_t));
        if (size < 1 || size > st.st_size)
        {
            rc = false;
            break;
        }

        rb_buf_t buf = __create_buf(addr, size);
        rc = load(&buf, obj_val);

    } while (0);

    if (MAP_FAILED != addr)
    {
        munmap(addr, st.st_size);
    }
    if (-1 != fd)
    {
        close(fd);
    }
    return rc;
}

#endif

uint32_t rb_crc32_long(void * p, rb_size_t size)
{
    uint8_t * pos = (uint8_t *) p;

    uint32_t  crc;

    crc = 0xffffffff;

    while (size--)
    {
        crc = rb_crc32_table256[(crc ^ *pos++) & 0xff] ^ (crc >> 8);
    }

    return crc ^ 0xffffffff;
}

rb_str_t rb_create_string(const char * str)
{
    rb_str_t result = { 0, 0 };
    if (str)
    {
        rb_str_t tmp = { (rb_size_t) strlen(str), (char *) str };
        rb_copy_to_string(&tmp, &result);
    }
    return result;
}

rb_bool_t rb_copy_to_string(const rb_str_t * src, rb_str_t * dst)
{
    if (!src || src->len < 1 || !src->data || !dst)
    {
        return false;
    }
    dst->len = src->len;
    dst->data = (char *) rb_malloc(dst->len + 1);
    memcpy(dst->data, src->data, dst->len);
    (dst->data)[dst->len] = '\0';
    return true;
}

rb_buf_t rb_create_buf(rb_size_t size)
{
    rb_buf_t buf;
    buf.start = (uint8_t *) rb_malloc(size);
    buf.pos = buf.start;
    buf.size = size;
    buf.end = buf.start + size;
    return buf;
}

void rb_dispose_buf(rb_buf_t * buf)
{
    if (!buf || !buf->start)
    {
        return;
    }
    rb_free(buf->start);
    memset(buf, 0, sizeof(rb_buf_t));
}

rb_buf_t rb_nested_buf(const rb_buf_t * buf, rb_offset_t offset)
{
    rb_buf_t nested_buf = { 0, 0, 0, 0 };
    if (rb_check_buf(buf))
    {
        nested_buf.start = (0 == offset) ? buf->pos : (buf->start + offset);
        nested_buf.end = buf->end;
        nested_buf.pos = nested_buf.start;
        nested_buf.size = nested_buf.end - nested_buf.start;
    }
    return nested_buf;
}

rb_bool_t rb_check_buf(const rb_buf_t * buf)
{
    return buf
        && buf->start
        && buf->pos
        && buf->end
        && buf->size > 0
        && (buf->pos >=buf->start)
        && (buf->pos <= buf->end)
        && (buf->start + buf->size <= buf->end);
}

rb_bool_t rb_encode_check(const rb_buf_t * buf, rb_size_t size)
{
    return rb_check_buf(buf) && buf->pos + size < buf->end;
}

rb_bool_t rb_decode_check(const rb_buf_t * buf, rb_offset_t offset, rb_size_t size)
{
    return rb_check_buf(buf)
        && (buf->start + offset + size < buf->end)
        && (offset + size < buf->size);
}

rb_bool_t rb_check_code(const rb_buf_t * buf, const rb_field_table_head_t * head)
{
    if (!head || !rb_check_buf(buf))
    {
        return false;
    }
    if (buf->start + head->size > buf->end || head->size > buf->size)
    {
        return false;
    }
    rb_size_t size = sizeof(rb_buf_end_t);
    uint8_t * pos = buf->start + (head->size - size);
    rb_buf_end_t end = 0;
    little_endian_copy(&end, pos, size);
    uint32_t checkcode = rb_crc32_long(buf->start, rb_seek_field_table_item(head->fields));
    if (end != checkcode)
    {
        return false;
    }
    return true;
}

rb_bool_t rb_set_buf_size(rb_size_t size, rb_buf_t * rb_val)
{
    uint8_t * pos = rb_val->start;
    rb_size_t length = sizeof(rb_size_t);
    if (rb_val->start + length > rb_val->end)
    {
        return false;
    }
    little_endian_copy(pos, &size, length);
    return true;
}

rb_size_t rb_seek_field_table_item(rb_field_size_t index)
{
    return sizeof(rb_field_table_head_t) + index * sizeof(rb_field_table_item_t);
}

rb_bool_t rb_set_field_count(rb_field_size_t fields, rb_buf_t * rb_val)
{
    rb_size_t size = sizeof(rb_field_table_head_t);
    if (rb_val->start + size > rb_val->end)
    {
        return false;
    }
    uint8_t * pos = rb_val->start + size;
    size = sizeof(rb_field_size_t);
    pos -= size;
    little_endian_copy(pos, &fields, size);
    rb_val->pos = rb_val->start + rb_seek_field_table_item(fields);
    if (rb_val->pos > rb_val->end)
    {
        return false;
    }
    return true;
}

rb_field_table_head_t rb_get_field_table_head(const rb_buf_t * rb_val)
{
    rb_field_table_head_t head = { 0, 0 };
    uint8_t * pos = rb_val->start;
    rb_size_t size = sizeof(rb_field_table_head_t);
    if (pos + size < rb_val->end)
    {
        size = sizeof(rb_size_t);
        little_endian_copy(&head.size, pos, size);
        little_endian_copy(&head.fields, pos + size, sizeof(rb_field_size_t));
    }
    return head;
}

rb_bool_t rb_set_field_table_item(rb_field_size_t index, rb_field_id_t id, rb_offset_t offset, rb_buf_t * rb_val)
{
    uint8_t * pos = rb_val->start + rb_seek_field_table_item(index);
    rb_size_t size = sizeof(rb_field_table_item_t);
    if (pos + size > rb_val->end)
    {
        return false;
    }
    size = sizeof(rb_field_id_t);
    little_endian_copy(pos, &id, size);
    little_endian_copy(pos + size, &offset, sizeof(rb_offset_t));
    return true;
}

rb_bool_t rb_get_field_table_item(rb_field_size_t index, const rb_buf_t * rb_val, rb_field_table_item_t * item)
{
    uint8_t * pos = rb_val->start + rb_seek_field_table_item(index);
    rb_size_t size = sizeof(rb_field_table_item_t);
    if (!item || (pos + size > rb_val->end))
    {
        return false;
    }
    size = sizeof(rb_field_id_t);
    little_endian_copy(&item->id, pos, size);
    little_endian_copy(&item->offset, pos + size, sizeof(rb_offset_t));
    return true;
}

rb_bool_t rb_encode_end(rb_field_size_t fields, rb_buf_t * rb_val)
{
    rb_size_t size = sizeof(rb_buf_end_t);
    if (!rb_check_buf(rb_val) || rb_val->pos + size > rb_val->end)
    {
        return false;
    }
    rb_buf_end_t end = 0;
    end = rb_crc32_long(rb_val->start, rb_seek_field_table_item(fields));
    little_endian_copy(rb_val->pos, &end, size);
    rb_val->pos += size;
    return true;
}

rb_size_t rb_seek_array_table_item(rb_size_t index)
{
    return sizeof(rb_size_t) + index * sizeof(rb_offset_t);
}

rb_bool_t rb_set_array_count(rb_size_t size, rb_buf_t * rb_val)
{
    if (!rb_check_buf(rb_val))
    {
        return false;
    }
    rb_size_t length = sizeof(rb_size_t);
    if (rb_val->pos + length > rb_val->end)
    {
        return false;
    }
    little_endian_copy(rb_val->pos, &size, length);
    rb_val->pos = rb_val->start + rb_seek_array_table_item(size);
    if (rb_val->pos > rb_val->end)
    {
        return false;
    }
    return true;
}

rb_size_t rb_get_array_count(const rb_buf_t * rb_val)
{
    rb_size_t size = 0;
    uint8_t * pos = rb_val->start;
    rb_size_t length = sizeof(rb_size_t);
    if (pos + length < rb_val->end)
    {
        little_endian_copy(&size, pos, length);
    }
    return size;
}

rb_bool_t rb_set_array_table_item(rb_size_t index, rb_offset_t offset, rb_buf_t * rb_val)
{
    uint8_t * pos = rb_val->start + rb_seek_array_table_item(index);
    rb_size_t size = sizeof(rb_offset_t);
    if (pos + size > rb_val->end)
    {
        return false;
    }
    little_endian_copy(pos, &offset, size);
    return true;
}

rb_bool_t rb_get_array_table_item(rb_size_t index, rb_buf_t * rb_val, rb_offset_t * item)
{
    uint8_t * pos = rb_val->start + rb_seek_array_table_item(index);
    rb_size_t size = sizeof(rb_offset_t);
    if (pos + size > rb_val->end)
    {
        return false;
    }
    little_endian_copy(item, pos, size);
    return true;
}

void rb_init_string(rb_str_t * obj_val)
{
    if (obj_val)
    {
        obj_val->len = 0;
        obj_val->data = 0;
    }
}

rb_bool_t rb_set_string(const rb_str_t * src, rb_str_t * dst)
{
    if (!src || !dst)
    {
        return false;
    }
    return rb_copy_to_string(src, dst);
}

rb_bool_t rb_eq_string(const rb_str_t * src, const rb_str_t * dst)
{
    if (!src || !dst)
    {
        return false;
    }
    if (!src->data && !dst->data)
    {
        return true;
    }
    if (!src->data || !dst->data || src->len != dst->len)
    {
        return false;
    }
    return 0 == memcmp(src->data, dst->data, src->len);
}

void rb_dispose_string(rb_str_t * obj_val)
{
    if (obj_val && obj_val->data)
    {
        rb_free(obj_val->data);
        obj_val->data = NULL;
        obj_val->len = 0;
    }
}

rb_size_t rb_sizeof_string(const rb_str_t * obj_val)
{
    return sizeof(rb_size_t) + (obj_val ? obj_val->len : 0);
}

rb_bool_t rb_encode_string(const rb_str_t * obj_val, rb_buf_t * rb_val)
{
    rb_size_t len = rb_sizeof_string(obj_val);
    if (!obj_val || !rb_encode_check(rb_val, len))
    {
        return false;
    }
    len = sizeof(rb_size_t);
    little_endian_copy(rb_val->pos, &obj_val->len, len);
    rb_val->pos += len;
    if (obj_val->data && obj_val->len > 0)
    {
        memcpy(rb_val->pos, obj_val->data, obj_val->len);
        rb_val->pos += obj_val->len;
    }
    return true;
}

rb_bool_t rb_decode_string(const rb_buf_t * rb_val, rb_offset_t offset, rb_str_t * obj_val)
{
    rb_size_t len = sizeof(rb_size_t);
    if (!obj_val || !rb_decode_check(rb_val, offset, len))
    {
        return false;
    }
    little_endian_copy(&obj_val->len, rb_val->start + offset, len);
    if (obj_val->len > 0)
    {
        offset += len;
        if (!rb_decode_check(rb_val, offset, obj_val->len))
        {
            return false;
        }
        obj_val->data = (char *) rb_malloc(obj_val->len + 1);
        memcpy(obj_val->data, rb_val->start + offset, obj_val->len);
        obj_val->data[obj_val->len] = '\0';
    }
    else
    {
        obj_val->data = (char *) rb_malloc(1);
        obj_val->data[0] = '\0';
    }
    return true;
}
