#!/usr/bin/python
#author: jobs
#email: yao050421103@gmail.com
import sys
import os.path
import datetime
import string
import json

CTYPE = 0
NAME = 1
ID = 2
KEY = 3 #append in runtime

FILTER = '@null_string_place_holder'
merge = lambda l: string.join(filter(lambda item: FILTER != item, l), '\n')
json_filter = lambda f: (lambda f, l: os.path.splitext(f)[1] in l)(f, ['.json'])

def manual(): 
    print """
    usage:
        python rawbuf.py [option] filelist
            [option]
                -f: use file in filelist
                -p: use dir in filelist, will be parsed recursive
                
    sample:
        python rawbuf.py -f file1.json file2.json file3.json
        python rawbuf.py -p ./dir1/ ./dir2/ ./dir3/
        """

def get_file_list(cur_dir, path_filter):
    def __get(cur_dir, path_filter, file_list):
        for root, dirs, files in os.walk(cur_dir): 
            for f in files:
                if path_filter(f):
                    file_list.append(os.path.join(root, f))
    file_list = []
    __get(cur_dir, path_filter, file_list)
    return file_list

def get_files(file_filter, op, urls):
    if '-f' == op:
        return filter(file_filter, urls)
    elif '-p' == op:
        file_set = set()
        for url in urls:
            for item in get_file_list(url, file_filter):
                if not item in file_set:
                    file_set.add(item)
        return list(file_set)
    return []

def write_file(url, data):
    with open(url, 'w') as f:
        f.writelines(data)

def get_rb_types():
    return [
        { 'key': 'bool', 'ctype': 'rb_bool_t', 'val': '0' },
        { 'key': 'int8', 'ctype': 'int8_t', 'val': '0' },
        { 'key': 'uint8', 'ctype': 'uint8_t', 'val': '0' },
        { 'key': 'int16', 'ctype': 'int16_t', 'val': '0' },
        { 'key': 'uint16', 'ctype': 'uint16_t', 'val': '0' },
        { 'key': 'int32', 'ctype': 'int32_t', 'val': '0' },
        { 'key': 'uint32', 'ctype': 'uint32_t', 'val': '0' },
        { 'key': 'int64', 'ctype': 'int64_t', 'val': '0' },
        { 'key': 'uint64', 'ctype': 'uint64_t', 'val': '0' },
        { 'key': 'float', 'ctype': 'float', 'val': '0.0' },
        { 'key': 'double', 'ctype': 'double', 'val': '0.0' }
        ]
def get_rb_str_t():
    return { 'key': 'string', 'ctype': 'rb_str_t' }

def write_interface(path, header, details):
    tm = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    head_def = '__%s_%s_h__' % (os.path.basename(path).lower(), tm)
    write_file(path + ".h", merge([
        header,
        '#ifndef %s' % head_def,
        '#define %s' % head_def,
        '',
        details,
        '#endif // %s' % head_def
        ]))
def create_nested_buf(args): 
    return merge([
    '    rb_buf_t buf = rb_nested_buf(rb_val, %s);' % args,
    '    if (buf.size < 1)',
    '    {',
    '        return false;',
    '    }',
    ])
def get_rb_methods():
    __pre_check_str = merge([
        '    if (!src || !dst)',
        '    {',
        '        return false;',
        '    }',
        ])
    __init = {
        'dec': lambda type: 'void rb_init_%s(%s * obj_val)' % (type['key'], type['ctype']),
        'imp': lambda type: merge([
            '    if (obj_val)',
            '    {',
            '        *obj_val = %s;' % type['val'],
            '    }',
            ])
        }
    __set = {
        'dec': lambda type: 'rb_bool_t rb_set_%s(const %s * src, %s * dst)' % (type['key'], type['ctype'], type['ctype']),
        'imp': lambda type: merge([
            __pre_check_str,
            '    *dst = *src;',
            '    return true;'
            ])
        }
    __eq = {
        'dec': lambda type: 'rb_bool_t rb_eq_%s(const %s * src, const %s * dst)' % (type['key'], type['ctype'], type['ctype']),
        'imp': lambda type: merge([
            __pre_check_str,
            '    return *src == *dst;'
            ])
        }
    __dispose = {
        'dec': lambda type: 'void rb_dispose_%s(%s * obj_val)' % (type['key'], type['ctype']),
        'imp': lambda type: merge([
            '    if (obj_val)',
            '    {',
            '        *obj_val = %s;' % type['val'],
            '    }'
            ])
        }
    __sizeof = {
        'dec': lambda type: 'rb_size_t rb_sizeof_%s(const %s * obj_val)' % (type['key'], type['ctype']),
        'imp': lambda type: '    return sizeof(%s);' % type['ctype']
        }
    __encode = {
        'dec': lambda type: 'rb_bool_t rb_encode_%s(const %s * obj_val, rb_buf_t * rb_val)' % (type['key'], type['ctype']),
        'imp': lambda type: merge([
            '    rb_size_t len = sizeof(%s);' % type['ctype'],
            '    if (!obj_val || !rb_encode_check(rb_val, len))',
            '    {',
            '        return false;',
            '    }',
            '    little_endian_copy(rb_val->pos, obj_val, len);',
            '    rb_val->pos += len;',
            '    return true;'
            ])
        }
    __decode = {
        'dec': lambda type: 'rb_bool_t rb_decode_%s(const rb_buf_t * rb_val, rb_offset_t offset, %s * obj_val)' % (type['key'], type['ctype']),
        'imp': lambda type: merge([
            '    rb_size_t len = sizeof(%s);' % type['ctype'],
            '    if (!obj_val || !rb_decode_check(rb_val, offset, len))',
            '    {',
            '        return false;',
            '    }',
            '    little_endian_copy(obj_val, rb_val->start + offset, len);',
            '    return true;'
            ])
        }
    return [__init, __set, __eq, __dispose, __sizeof, __encode, __decode]

def get_array_frame():
    __create = lambda base, key, ctype: merge([
        '    %s_%s_t obj_val = { capacity, 0, 0 };' % (key, base['type']),
        '    if (capacity > 0)',
        '    {',
        base['len'](key, ctype),
        '        obj_val.arr = (%s *) rb_malloc(len);' % base['cast'],
        '        memset(obj_val.arr, 0, len);',
        '        rb_size_t i = 0;',
        '        for (i = 0; i < capacity; ++i)',
        '        {',
        base['init'](key, ctype),
        '        }',
        '    }',
        '    return obj_val;'
        ])
    __init = lambda base, key, ctype: merge([
        '    if (!obj_val || !obj_val->arr || obj_val->capacity < 1)',
        '    {',
        '        return;',
        '    }',
        '    rb_size_t i = 0;',
        '    for (i = 0; i < obj_val->capacity; ++i)',
        '    {',
        base['init'](key, ctype),
        '    }'
        ])
    __set = lambda base, key, ctype: merge([
        '    if(!src || !src->arr || !dst)',
        '    {',
        '        return false;',
        '    }',
        '    if (src->size < 1)',
        '    {',
        '        memset(dst, 0, sizeof(%s_%s_t));' % (key, base['type']),
        '        return true;',
        '    }',
        '    *dst = rb_create_%s_%s(src->size);' % (key, base['type']),
        '    dst->size = src->size;',
        '    rb_size_t i = 0;',
        '    for (i = 0; i < dst->size; ++i)',
        '    {',
        base['set'](key, ctype),
        '    }',
        '    return true;'
        ])
    __eq = lambda base, key, ctype: merge([
        '    if(!src || !dst)',
        '    {',
        '        return false;',
        '    }',
        '    if (!src->arr && !dst->arr)',
        '    {',
        '        return true;',
        '    }',
        '    if(!src->arr || !dst->arr || (src->size != dst->size))',
        '    {',
        '        return false;',
        '    }',
        '    rb_size_t i = 0;',
        '    for (i = 0; i < src->size; ++i)',
        '    {',
        base['eq'](key, ctype),
        '        {',
        '            return false;',
        '        }',
        '    }',
        '    return true;'
        ])
    __dispose = lambda base, key, ctype: merge([
        '    if (!obj_val || !obj_val->arr)',
        '    {',
        '        return;',
        '    }',
        '    rb_size_t i = 0;',
        '    for (i = 0; i < obj_val->size; ++i)',
        '    {',
        base['dispose'](key, ctype),
        '    }',
        '    rb_free(obj_val->arr);',
        '    memset(obj_val, 0, sizeof(%s_%s_t));' % (key, base['type'])
        ])
    __sizeof = lambda base, key, ctype: merge([
        '    rb_size_t size = sizeof(rb_size_t) + obj_val->size * sizeof(rb_size_t);',
        '    rb_size_t i = 0;',
        '    for (i = 0; i < obj_val->size; ++i)',
        '    {',
        base['sizeof'](key, ctype),
        '    }',
        '    return size;'
        ])
    __encode = lambda base, key, ctype: merge([
        '    if (!obj_val || !obj_val->arr)',
        '    {',
        '        return false;',
        '    }',
        create_nested_buf('0'),
        '    if (!rb_set_array_count(obj_val->size, &buf))',
        '    {',
        '        return false;',
        '    }',
        '    rb_size_t i = 0;',
        '    for (i = 0; i < obj_val->size; ++i)',
        '    {',
        '        if (!rb_set_array_table_item(i, buf.pos - buf.start, &buf))',
        '        {',
        '            return false;',
        '        }',
        base['encode'](key, ctype),
        '        {',
        '            return false;',
        '        }',
        '    }',
        '    rb_val->pos = buf.pos;',
        '    return true;'
        ])
    __decode = lambda base, key, ctype: merge([
        '    if (!obj_val)',
        '    {',
        '        return false;',
        '    }',
        create_nested_buf('offset'),
        '    rb_size_t size = rb_get_array_count(&buf);',
        '    if (size < 1)',
        '    {',
        '        memset(obj_val, 0, sizeof(%s_%s_t));' % (key, base['type']),
        '        return true;',
        '    }',
        '',
        '    *obj_val = rb_create_%s_%s(size);' % (key, base['type']),
        '    obj_val->size = size;',
        '',
        '    rb_bool_t rc = true;',
        '    rb_offset_t off = 0;',
        '    rb_size_t i = 0;',
        '    for (i = 0; i < size; ++i)',
        '    {',
        '        if (!rb_get_array_table_item(i, &buf, &off))',
        '        {',
        '            rc = false;',
        '            break;',
        '        }',
        base['decode'](key, ctype),
        '        {',
        '            rc = false;',
        '            break;',
        '        }',
        '    }',
        '    if (!rc)',
        '    {',
        '        rb_dispose_%s_%s(obj_val);' % (key, base['type']),
        '    }',
        '    return rc;'
        ])
    return {
        'create': __create,
        'init': __init,
        'set': __set,
        'eq': __eq,
        'dispose': __dispose,
        'sizeof': __sizeof,
        'encode': __encode,
        'decode': __decode
        }
def gen_array_def(key, ctype):
    return merge([
    'typedef struct',
    '{',
    '    rb_size_t capacity;',
    '    rb_size_t size;',
    '    %s * arr;' % ctype,
    '} %s_array_t;' % key,
    ''
    ])
def gen_array_imp(key, ctype, method): 
    return merge([
        method['dec'](key, ctype),
        '{',
        method['imp'](key, ctype),
        '}',
        ''
        ])

def get_array_methods(array_frame):
    __create = {
        'dec': lambda key, ctype: '%s_array_t rb_create_%s_array(rb_size_t capacity)' % (key, key),
        'imp': lambda key, ctype: array_frame['create']({
            'type': 'array',
            'cast': ctype,
            'len': lambda key, ctype: '        rb_size_t len = capacity * sizeof(%s);' % ctype,
            'init': lambda key, ctype: '            rb_init_%s(obj_val.arr + i);' % key,
            }, key, ctype)
        }
    __append_to = {
        'dec': lambda key, ctype: 'rb_bool_t rb_append_to_%s_array(const %s * item, %s_array_t * obj_val)' % (key, ctype, key),
        'imp': lambda key, ctype: merge([
            '    if (!item || !obj_val || !obj_val->arr || obj_val->size >= obj_val->capacity)',
            '    {',
            '        return false;',
            '    }',
            '    %s * dst = obj_val->arr + obj_val->size;' % ctype,
            '    if (rb_set_%s(item, dst))' % key,
            '    {',
            '        ++obj_val->size;',
            '        return true;',
            '    }',
            '    return false;'
            ])
        }
    __init = {
        'dec': lambda key, ctype: 'void rb_init_%s_array(%s_array_t * obj_val)' % (key, key),
        'imp': lambda key, ctype: array_frame['init']({
            'init': lambda key, ctype: '        rb_init_%s(obj_val->arr + i);' % key
            }, key, ctype)
        }
    __set = {
        'dec': lambda key, ctype: 'rb_bool_t rb_set_%s_array(const %s_array_t * src, %s_array_t * dst)' % (key, key, key),
        'imp': lambda key, ctype: array_frame['set']({
            'type': 'array',
            'set': lambda key, ctype: merge([
                '        if (!rb_set_%s(src->arr + i, dst->arr + i))' % key,
                '        {',
                '            rb_dispose_%s_array(dst);' % key,
                '            return false;',
                '        }',
                ])
            }, key, ctype)
        }
    __eq = {
        'dec': lambda key, ctype: 'rb_bool_t rb_eq_%s_array(const %s_array_t * src, const %s_array_t * dst)' % (key, key, key),
        'imp': lambda key, ctype: array_frame['eq']({
            'type': 'array',
            'eq': lambda key, ctype: '        if (!rb_eq_%s(src->arr + i, dst->arr + i))' % key
            }, key, ctype)
        }
    __dispose = {
        'dec': lambda key, ctype: 'void rb_dispose_%s_array(%s_array_t * obj_val)' % (key, key),
        'imp': lambda key, ctype: array_frame['dispose']({
            'type': 'array',
            'dispose': lambda key, ctype: '        rb_dispose_%s(obj_val->arr + i);' % key
            }, key, ctype)
        }
    __sizeof = {
        'dec': lambda key, ctype: 'rb_size_t rb_sizeof_%s_array(const %s_array_t * obj_val)' % (key, key),
        'imp': lambda key, ctype: array_frame['sizeof']({
            'sizeof': lambda key, ctype: '        size += rb_sizeof_%s(obj_val->arr + i);' % key
            }, key, ctype)
        }
    __encode = {
        'dec': lambda key, ctype: 'rb_bool_t rb_encode_%s_array(const %s_array_t * obj_val, rb_buf_t * rb_val)' % (key, key),
        'imp': lambda key, ctype: array_frame['encode']({
            'encode': lambda key, ctype: '        if (!rb_encode_%s(obj_val->arr + i, &buf))' % key
            }, key, ctype)
        }
    __decode = {
        'dec': lambda key, ctype: 'rb_bool_t rb_decode_%s_array(const rb_buf_t * rb_val, rb_offset_t offset, %s_array_t * obj_val)' % (key, key),
        'imp': lambda key, ctype: array_frame['decode']({
            'type': 'array',
            'decode': lambda key, ctype: '        if (!rb_decode_%s(&buf, off, obj_val->arr + i))' % key
            }, key, ctype)
        }
    return [__create, __append_to, __init, __set, __eq, __dispose, __sizeof, __encode, __decode]

def gen_dict_def(key, ctype):
    return merge([
    'typedef struct',
    '{',
    '    rb_str_t key;',
    '    %s val;' % ctype,
    '} %s_pair_t;' % key,
    '',
    'typedef struct',
    '{',
    '    rb_size_t capacity;',
    '    rb_size_t size;',
    '    %s_pair_t * arr;' % key,
    '} %s_dict_t;' % key,
    ''
    ])
def get_dict_methods(array_frame):
    __create = {
        'dec': lambda key, ctype: '%s_dict_t rb_create_%s_dict(rb_size_t capacity)' % (key, key),
        'imp': lambda key, ctype: array_frame['create']({
            'type': 'dict',
            'cast': '%s_pair_t' % key,
            'len': lambda key, ctype: '        rb_size_t len = capacity * sizeof(%s_pair_t);' % key,
            'init': lambda key, ctype: merge([
                '            rb_init_string(&(obj_val.arr + i)->key);',
                '            rb_init_%s(&(obj_val.arr + i)->val);' % key
                ])
            }, key, ctype)
        }
    __get_item = {
        'dec': lambda key, ctype: '%s_pair_t * rb_%s_dict_get_item(const %s_dict_t * obj_val, const rb_str_t * key)' % (key, key, key),
        'imp': lambda key, ctype: merge([
            '    if (!obj_val || !key || obj_val->size < 1 || obj_val->capacity < 1)',
            '    {',
            '        return NULL;',
            '    }',
            '    rb_size_t i = 0;',
            '    for (i = 0; i < obj_val->size; ++i)',
            '    {',
            '        %s_pair_t * item = obj_val->arr + i;' % key,
            '        if (rb_eq_string(key, &item->key))',
            '        {',
            '            return item;',
            '        }',
            '    }',
            '    return NULL;'
            ])
        }
    __set_item = {
        'dec': lambda key, ctype: 'rb_bool_t rb_%s_dict_set_item(const rb_str_t * key, const %s * val, %s_dict_t * obj_val)' % (key, ctype, key),
        'imp': lambda key, ctype: merge([
            '    if (!key || !val || !obj_val || !obj_val->arr || obj_val->size >= obj_val->capacity)',
            '    {',
            '        return false;',
            '    }',
            '    %s_pair_t * it = rb_%s_dict_get_item(obj_val, key);' % (key, key),
            '    if (it)',
            '    {',
            '        rb_dispose_%s(&it->val);' % key,
            '        return rb_set_%s(val, &it->val);' % key,
            '    }',
            '    it = obj_val->arr + obj_val->size;',
            '    if (!rb_set_string(key, &it->key))',
            '    {',
            '        return false;',
            '    }',
            '    if (!rb_set_%s(val, &it->val))' % key,
            '    {',
            '        rb_dispose_string(&it->key);',
            '        return false;',
            '    }',
            '    ++obj_val->size;',
            '    return false;'
            ])
        }
    __init = {
        'dec': lambda key, ctype: 'void rb_init_%s_dict(%s_dict_t * obj_val)' % (key, key),
        'imp': lambda key, ctype: array_frame['init']({
            'init': lambda key, ctype: merge([
                '        %s_pair_t * it = obj_val->arr + i;' % key,
                '        rb_init_string(&it->key);',
                '        rb_init_%s(&it->val);' % key
                ])
            }, key, ctype)
        }
    __set = {
        'dec': lambda key, ctype: 'rb_bool_t rb_set_%s_dict(const %s_dict_t * src, %s_dict_t * dst)' % (key, key, key),
        'imp': lambda key, ctype: array_frame['set']({
            'type': 'dict',
            'set': lambda key, ctype: merge([
                '        %s_pair_t * it_src = src->arr + i;' % key,
                '        %s_pair_t * it_dst = dst->arr + i;' % key,
                '        if (!rb_set_string(&it_src->key, &it_dst->key))',
                '        {',
                '            rb_dispose_%s_dict(dst);' % key,
                '            return false;',
                '        }',
                '        if (!rb_set_%s(&it_src->val, &it_dst->val))' % key,
                '        {',
                '            rb_dispose_%s_dict(dst);' % key,
                '            return false;',
                '        }'
                ])
            }, key, ctype)
        }
    __eq = {
        'dec': lambda key, ctype: 'rb_bool_t rb_eq_%s_dict(const %s_dict_t * src, const %s_dict_t * dst)' % (key, key, key),
        'imp': lambda key, ctype: array_frame['eq']({
            'type': 'dict',
            'eq': lambda key, ctype: merge([
                '        %s_pair_t * it_src = src->arr + i;' % key,
                '        %s_pair_t * it_dst = dst->arr + i;' % key,
                '        if (!rb_eq_string(&it_src->key, &it_dst->key))',
                '        {',
                '            return false;',
                '        }',
                '        if (!rb_eq_%s(&it_src->val, &it_dst->val))' % key
                ])
            }, key, ctype)
        }
    __dispose = {
        'dec': lambda key, ctype: 'void rb_dispose_%s_dict(%s_dict_t * obj_val)' % (key, key),
        'imp': lambda key, ctype: array_frame['dispose']({
            'type': 'dict',
            'dispose': lambda key, ctype: merge([
                '        %s_pair_t * it = obj_val->arr + i;' % key,
                '        rb_dispose_string(&it->key);',
                '        rb_dispose_%s(&it->val);' % key
                ])
            }, key, ctype)
        }
    __sizeof = {
        'dec': lambda key, ctype: 'rb_size_t rb_sizeof_%s_dict(const %s_dict_t * obj_val)' % (key, key),
        'imp': lambda key, ctype: array_frame['sizeof']({
            'sizeof': lambda key, ctype: merge([
                '        %s_pair_t * it = obj_val->arr + i;' % key,
                '        size += rb_sizeof_string(&it->key);',
                '        size += rb_sizeof_%s(&it->val);' % key
                ])
            }, key, ctype)
        }
    __encode = {
        'dec': lambda key, ctype: 'rb_bool_t rb_encode_%s_dict(const %s_dict_t * obj_val, rb_buf_t * rb_val)' % (key, key),
        'imp': lambda key, ctype: array_frame['encode']({
            'encode': lambda key, ctype: merge([
                '        %s_pair_t * it = obj_val->arr + i;' % key,
                '        if (!rb_encode_string(&it->key, &buf))',
                '        {',
                '            return false;',
                '        }',
                '        if (!rb_encode_%s(&it->val, &buf))' % key
                ])
            }, key, ctype)
        }
    __decode = {
        'dec': lambda key, ctype: 'rb_bool_t rb_decode_%s_dict(const rb_buf_t * rb_val, rb_offset_t offset, %s_dict_t * obj_val)' % (key, key),
        'imp': lambda key, ctype: array_frame['decode']({
            'type': 'dict',
            'decode': lambda key, ctype: merge([
                '        %s_pair_t * it = obj_val->arr + i;' % key,
                '        if (!rb_decode_string(&buf, off, &it->key))',
                '        {',
                '            rc = false;',
                '            break;',
                '        }',
                '        rb_offset_t delta = rb_sizeof_string(&it->key);',
                '        if (!rb_decode_%s(&buf, off + delta, &it->val))' % key
                ])
            }, key, ctype)
        }
    return [__create, __get_item, __set_item, __init, __set, __eq, __dispose, __sizeof, __encode, __decode]

def get_header():
    return merge([
        '////////////////////////////////////////////////////////////////////////////////',
        '// NOTE : Generated by rawbuf. It is NOT supposed to modify this file.',
        '////////////////////////////////////////////////////////////////////////////////'
        ])
def include_base():
    return merge([
    '#ifdef WIN32',
    '#define true  1',
    '#define false 0',
    '#else',
    '#include <stdbool.h>',
    '#endif',
    '',
    ])

def gen_rawbuf(path, types, str_t, methods, array_methods, dict_methods):
    def __gen_interface(path, types, full_types, methods, array_methods, dict_methods):
        __gen_dec = lambda type, method: method['dec'](type) + ';'
        __gen_array_dec = lambda type, method: method['dec'](type['key'], type['ctype']) + ';'
        write_interface(path, get_header(), merge([
            '#include "rawbuf_utils.h"',
            '',
            merge([merge([__gen_dec(type, method) for type in types]) + '\n' for method in methods]),
            merge([merge([
                gen_array_def(type['key'], type['ctype']),
                merge([__gen_array_dec(type, method) for method in array_methods]),
                ''
                ]) for type in full_types]),
            merge([merge([
                gen_dict_def(type['key'], type['ctype']),
                merge([__gen_array_dec(type, method) for method in dict_methods]),
                ''
                ]) for type in full_types]),
            ]))
    def __gen_implement(path, types, full_types, methods, array_methods, dict_methods):
        __gen_imp = lambda type, method: merge([
            method['dec'](type),
            '{',
            method['imp'](type),
            '}',
            ''
            ])
        write_file(path + ".c", merge([
            get_header(),
            '#include "%s.h"' % os.path.basename(path),
            include_base(),
            merge([merge([__gen_imp(type, method) for type in types]) for method in methods]),
            merge([merge([gen_array_imp(type['key'], type['ctype'], method) for method in array_methods]) for type in full_types]),
            merge([merge([gen_array_imp(type['key'], type['ctype'], method) for method in dict_methods]) for type in full_types]),
            ''
            ]))
    __full_types = list(types)
    __full_types.append(str_t)
    __gen_interface(path, types, __full_types, methods, array_methods, dict_methods)
    __gen_implement(path, types, __full_types, methods, array_methods, dict_methods)
    return True

def get_object_methods():
    __do_while_frame = lambda impl: merge([
        '    do',
        '    {',
        impl,
        '',
        '        return true;',
        '    } while (0);',
        '',
        '    return false;'
        ])
    __pre_check_str = merge([
        '    if (!obj_val)',
        '    {',
        '        return;',
        '    }',
        ])
    __pre_check_pair_str = merge([
        '    if (!src || !dst)',
        '    {',
        '        return false;',
        '    }',
        ])
    __init = {
        'dec': lambda key, ctype: 'void rb_init_%s(%s * obj_val)' % (key, ctype),
        'imp': lambda key, ctype, members: merge([
            __pre_check_str,
            '    memset(obj_val, 0, sizeof(%s));' % ctype,
            merge([merge([
                '',
                '    rb_init_%s(&obj_val->%s);' % (member[KEY], member[NAME]),
                '    obj_val->id_%s = %s;' % (member[NAME], member[ID]),
                '    obj_val->skip_%s = false;' % member[NAME],
                '    obj_val->rb_has_%s = false;' % member[NAME]
                ]) for member in members])
            ])
        }
    __set = {
        'dec': lambda key, ctype: 'rb_bool_t rb_set_%s(const %s * src, %s * dst)' % (key, ctype, ctype),
        'imp': lambda key, ctype, members: merge([
            __pre_check_pair_str,
            merge(['    dst->id_%s = src->id_%s;' % (member[NAME], member[NAME]) for member in members]),
            __do_while_frame(merge(['        if (!rb_set_%s(&src->%s, &dst->%s)) break;' % (
                member[KEY], member[NAME], member[NAME]) for member in members])),
            ])
        }
    __eq = {
        'dec': lambda key, ctype: 'rb_bool_t rb_eq_%s(const %s * src, const %s * dst)' % (key, ctype, ctype),
        'imp': lambda key, ctype, members: merge([
            __pre_check_pair_str,
            __do_while_frame(merge(['        if (!rb_eq_%s(&src->%s, &dst->%s)) break;' % (
                member[KEY], member[NAME], member[NAME]) for member in members]))
            ])
        }
    __dispose = {
        'dec': lambda key, ctype: 'void rb_dispose_%s(%s * obj_val)' % (key, ctype),
        'imp': lambda key, ctype, members: merge([
            __pre_check_str,
            merge(['    rb_dispose_%s(&obj_val->%s);' % (member[KEY], member[NAME])  for member in members])
            ])
        }
    __rb_fields = {
        'dec': lambda key, ctype: 'rb_field_size_t rb_fields_%s(const %s * obj_val)' % (key, ctype),
        'imp': lambda key, ctype, members: merge([
            '    rb_field_size_t fields = 0;',
            merge(['    if (!obj_val->skip_%s) ++fields;' % member[NAME] for member in members]),
            '    return fields;'
            ])
        }
    __sizeof = {
        'dec': lambda key, ctype: 'rb_size_t rb_sizeof_%s(const %s * obj_val)' % (key, ctype),
        'imp': lambda key, ctype, members: merge([
            '    rb_field_size_t fields = 0;',
            '    rb_size_t size = 0;',
            merge([merge([
                '    if (!obj_val->skip_%s)' % member[NAME],
                '    {',
                '        size += rb_sizeof_%s(&obj_val->%s);' % (member[KEY], member[NAME]),
                '        ++fields;',
                '    }',
                ]) for member in members]),
            '    size += rb_seek_field_table_item(fields);',
            '    size += sizeof(rb_buf_end_t);',
            '    return size;'
            ])
        }
    __encode = {
        'dec': lambda key, ctype: 'rb_bool_t rb_encode_%s(const %s * obj_val, rb_buf_t * rb_val)' % (key, ctype),
        'imp': lambda key, ctype, members: merge([
            create_nested_buf('0'),
            __do_while_frame(merge([
                '        rb_field_size_t fields = rb_fields_%s(obj_val);' % key,
                '        rb_field_size_t index = 0;',
                '        if (!rb_set_field_count(fields, &buf)) break;',
                '',
                merge([merge([
                    '        if (!obj_val->skip_%s)' % member[NAME],
                    '        {',
                    '            if (!rb_set_field_table_item(index++, obj_val->id_%s, buf.pos - buf.start, &buf)) break;' % member[NAME],
                    '            if (!rb_encode_%s(&obj_val->%s, &buf)) break;' % (member[KEY], member[NAME]),
                    '        }',
                    ]) for member in members]),
                '',
                '        if (!rb_set_buf_size(buf.pos - buf.start + sizeof(rb_buf_end_t), &buf)) break;',
                '        if (!rb_encode_end(fields, &buf)) break;',
                '        rb_val->pos = buf.pos;',
                ]))
            ])
        }
    __decode = {
        'dec': lambda key, ctype: 'rb_bool_t rb_decode_%s(const rb_buf_t * rb_val, rb_offset_t offset, %s * obj_val)' % (key, ctype),
        'private_imp': lambda key, ctype, members: merge([
            'static rb_bool_t __decode_%s(' % key,
            '    const rb_field_table_item_t * item,',
            '    const rb_buf_t * rb_val,',
            '    %s * obj_val)' % ctype,
            '{',
            merge([merge([
                '    if (item->id == obj_val->id_%s)' % member[NAME],
                '    {',
                '        rb_bool_t rc = rb_decode_%s(rb_val, item->offset, &obj_val->%s);' % (member[KEY], member[NAME]),
                '        if (rc)',
                '        {',
                '            obj_val->rb_has_%s = true;' % member[NAME],
                '        }',
                '        return rc;',
                '    }',
                ]) for member in members]),
            '    return true;',
            '}',
            ''
            ]),
        'imp': lambda key, ctype, members: merge([
            '    if (!obj_val)',
            '    {',
            '        return false;',
            '    }',
            create_nested_buf('offset'),
            '    rb_field_table_head_t head = rb_get_field_table_head(&buf);',
            '    if (head.fields < 1 || !rb_check_code(&buf, &head))',
            '    {',
            '        return false;',
            '    }',
            '    rb_field_table_item_t item = { 0, 0 };',
            '    rb_field_size_t i = 0;',
            '    for (i = 0; i < head.fields; ++i)',
            '    {',
            '        if (!rb_get_field_table_item(i, &buf, &item))',
            '        {',
            '            return false;',
            '        }',
            '        if (item.offset >= head.size)',
            '        {',
            '            return false;',
            '        }',
            '        if (item.offset > 0 && !__decode_%s(&item, &buf, obj_val))' % key,
            '        {',
            '            return false;',
            '        }',
            '    }',
            '    return true;',
            ])
        }
    __dump = {
        'dec': lambda key, ctype: 'rb_bool_t rb_dump_%s(const %s * obj_val, const char * path)' % (key, ctype),
        'private_imp': lambda key, ctype, members: merge([
            'static rb_bool_t __dump_%s(const void * obj_val, rb_buf_t * buf)' % key,
            '{',
            '    return rb_encode_%s((%s *) obj_val, buf);' % (key, ctype),
            '}',
            ''
            ]),
        'imp': lambda key, ctype, members: merge([
            '    if (!obj_val || !path)',
            '    {',
            '        return false;',
            '    }',
            '    rb_size_t size = rb_sizeof_%s(obj_val);' % key,
            '    if (size < 1)',
            '    {',
            '        return false;',
            '    }',
            '    return rb_dump_buf(__dump_%s, obj_val, size, path);' % key,
            ])
        }
    __load = {
        'dec': lambda key, ctype: 'rb_bool_t rb_load_%s(const char * path, %s * obj_val)' % (key, ctype),
        'private_imp': lambda key, ctype, members: merge([
            'static rb_bool_t __load_%s(const rb_buf_t * buf, void * obj_val)' % key,
            '{',
            '    return rb_decode_%s(buf, 0, (%s *) obj_val);' % (key, ctype),
            '}',
            ''
            ]),
        'imp': lambda key, ctype, members: '    return rb_load_buf(path, __load_%s, obj_val);' % key
        }
    return [__init, __set, __eq, __dispose, __rb_fields, __sizeof, __encode, __decode, __dump, __load]

def gen_from_schema(path, obj, types, object_methods, array_methods, dict_methods):
    gen_array = lambda struct: 'gen_array' in struct and struct['gen_array']
    def __check(structs):
        for struct in structs:
            ctype = struct['type']
            if not ctype.endswith('_t'):
                print '"%s" is not end with "_t"' % ctype
                return False
            ids = set()
            for member in struct['members']:
                if len(member) > (KEY) or len(member) < (ID):
                    print 'invalid members: "%s" in struct "%s"' % (str(member), ctype)
                    return False
                if len(member) < (ID + 1):
                    continue
                id = member[ID]
                if int(id) > 255:
                    print 'invalid id (should be: [0, 255]): "%s" in struct "%s"' % (str(member), ctype)
                    return False
                if id in ids:
                    print '"%s" duplicated in "%s"' % (str(id), ctype)
                    return False
                else:
                    ids.add(id)
        return True
    def __get_key(types, ctype):
        for type in types:
            if ctype == type['ctype']:
                return type['key']
        if ctype.endswith('_t'):
            return ctype[:(len(ctype) - len('_t'))]
        return ctype
    def __get_ctype(key, types):
        # do NOT support recursion!!!
        is_array = key.startswith('[') and key.endswith(']')
        is_dict = key.startswith('{') and key.endswith('}')
        if is_array:
            base_type = key[1:len(key) - 1]
            if 'string' == base_type:
                return 'string_array_t'
            return '%s_array_t' % __get_key(types, base_type)
        if is_dict:
            base_type = key[1:len(key) - 1]
            if 'string' == base_type:
                return 'string_dict_t'
            return '%s_dict_t' % __get_key(types, base_type)
        if 'string' == key:
            return 'rb_str_t'
        return key
    def __update_object(obj, types):
        def __update_ids(members):
            ids = [member[ID] for member in filter(lambda member: len(member) > ID, members)]
            default_ids = [str(members.index(member)) for member in members]
            for id in default_ids:
                if id in ids:
                    default_ids.remove(id)
            for member in members:
                if not len(member) > ID:
                    id = default_ids[0]
                    member.append(id)
                    default_ids.remove(id)
        size = len(obj['structs'])
        for struct in obj['structs']:
            if size - 1 == obj['structs'].index(struct):
                struct['gen_array'] = False
            else:
                struct['gen_array'] = True
            struct['key'] = __get_key(types, struct['type'])
            struct['ctype'] = struct['type']
            __update_ids(struct['members'])
            for member in struct['members']:
                member[CTYPE] = __get_ctype(member[CTYPE], types)
                member.append(__get_key(types, member[CTYPE]))
    def __gen_interface(path, obj, object_methods, array_methods, dict_methods):
        __get_ctype = lambda member: 'rb_bool_t' if 'bool' == member[CTYPE] else member[CTYPE]
        def __gen_struct(struct, object_methods, array_methods, dict_methods):
            __gen_def = lambda ctype, members: merge([
                'typedef struct',
                '{',
                merge(['    %s %s;' % (__get_ctype(member), member[NAME]) for member in members]),
                '',
                merge(['    rb_field_id_t id_%s;' % member[NAME] for member in members]),
                '',
                merge(['    rb_bool_t skip_%s;' % member[NAME] for member in members]),
                '',
                merge(['    rb_bool_t rb_has_%s;' % member[NAME] for member in members]),
                '} %s;' % ctype,
                ''
                ])
            __gen_dec = lambda key, ctype, method: method['dec'](key, ctype) + ';'
            __gen_array_dec = lambda key, ctype, method: method['dec'](key, ctype) + ';'
            __gen_array_interface = lambda struct, array_methods, dict_methods: merge([
                '',
                gen_array_def(struct['key'], struct['ctype']),
                merge([__gen_array_dec(struct['key'], struct['ctype'], method) for method in array_methods]),
                '',
                gen_dict_def(struct['key'], struct['ctype']),
                merge([__gen_array_dec(struct['key'], struct['ctype'], method) for method in dict_methods]),
                ''
                ]) if gen_array(struct) else FILTER
            return merge([
                __gen_def(struct['ctype'], struct['members']),
                merge([__gen_dec(struct['key'], struct['ctype'], method) for method in object_methods]),
                __gen_array_interface(struct, array_methods, dict_methods)
                ])
        write_interface(path, get_header(), merge([
            '#include "rawbuf.h"',
            '',
            merge([__gen_struct(struct, object_methods, array_methods, dict_methods) for struct in obj['structs']]),
            ''
            ]))
    def __gen_implement(path, obj, object_methods, array_methods, dict_methods):
        def __gen_struct(struct, object_methods, array_methods, dict_methods):
            __gen_imp = lambda key, ctype, members, method: merge([
                method['private_imp'](key, ctype, members) if 'private_imp' in method else FILTER,
                method['dec'](key, ctype),
                '{',
                method['imp'](key, ctype, members),
                '}',
                ''
                ])
            __gen_object_implement = lambda key, ctype, members, methods: merge([__gen_imp(key, ctype, members, method) for method in methods])
            __gen_array_imp = lambda key, ctype, methods: merge([
                gen_array_imp(key, ctype, method) for method in methods
                ])
            __gen_array_implement = lambda key, ctype, array_methods, dict_methods: merge([
                __gen_array_imp(key, ctype, array_methods),
                __gen_array_imp(key, ctype, dict_methods)
                ])
            return merge([
                __gen_object_implement(struct['key'], struct['ctype'], struct['members'], object_methods),
                __gen_array_implement(struct['key'], struct['ctype'], array_methods, dict_methods) if gen_array(struct) else FILTER
                ])
        write_file(path + ".c", merge([
            get_header(),
            '#include "%s.h"' % os.path.basename(path),
            include_base(),
            merge([__gen_struct(struct, object_methods, array_methods, dict_methods) for struct in obj['structs']])
            ]))
    if not __check(obj['structs']):
        return False
    __update_object(obj, types)
    __gen_interface(path, obj, object_methods, array_methods, dict_methods)
    __gen_implement(path, obj, object_methods, array_methods, dict_methods)
    return True

def gen(file_list, types, str_t, object_methods, array_methods, dict_methods):
    full_types = list(types)
    full_types.append(str_t)
    for path_item in file_list:
        with open(path_item, 'r') as f:
            obj = json.load(f)
            gen_from_schema(
                path_item[:path_item.rfind('.')], 
                obj, 
                full_types,
                object_methods,
                array_methods,
                dict_methods)
    return True

def parse_shell(argv):
    def __get_path(argv):
        __path = '.' if 2 != len(argv) else argv[1]
        return os.path.join(os.path.abspath(__path), 'rawbuf')
    size = len(argv)
    array_frame = get_array_frame()
    if 1 == size or 2 == size:
        return gen_rawbuf(
            __get_path(argv), 
            get_rb_types(), 
            get_rb_str_t(), 
            get_rb_methods(), 
            get_array_methods(array_frame),
            get_dict_methods(array_frame))
    op = argv[1]
    file_list = get_files(json_filter, op, argv[2:])
    return gen(
        file_list, 
        get_rb_types(), 
        get_rb_str_t(), 
        get_object_methods(),
        get_array_methods(array_frame),
        get_dict_methods(array_frame)
        ) if len(file_list) > 0 else False

if __name__ == "__main__":
    if not parse_shell(sys.argv):
        manual()