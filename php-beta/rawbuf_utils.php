<?php

const sizeof_bool = 1;
const sizeof_int8 = 1;
const sizeof_uint8 = 1;
const sizeof_int16 = 2;
const sizeof_uint16 = 2;
const sizeof_int32 = 4;
const sizeof_uint32 = 4;
const sizeof_int64 = 8;
const sizeof_uint64 = 8;
const sizeof_float = 4;
const sizeof_double = 8;

const sizeof_rb_size = sizeof_uint32;
const sizeof_rb_field_size = sizeof_uint8;
const sizeof_rb_field_id = sizeof_rb_field_size;
const sizeof_rb_offset = sizeof_rb_size;
const sizeof_rb_buf_end = sizeof_uint32;

define('rb_field_table_head_size', (sizeof_rb_size + sizeof_rb_field_size));
define('rb_field_table_item_size', (sizeof_rb_field_id + sizeof_rb_offset));

function rb_is_little_endian()
{
    static $_is_little_endian = null;
    if ($_is_little_endian === null)
    {
        $rc = unpack('S', "\x01\x00");
        $_is_little_endian = ($rc[1] === 1);
    }
    return $_is_little_endian;
}

function rb_write_little_endian($data, $offset, $count, &$buf)
{
    if (rb_is_little_endian())
    {
        for ($i = 0; $i < $count; $i++)
        {
            $buf['data'][$offset + $i] = chr($data >> $i * 8);
        }
    }
    else
    {
        for ($i = 0; $i < $count; $i++)
        {
            $buf['data'][$offset + $count - 1 - $i] = chr($data >> $i * 8);
        }
    }
}

function rb_read_little_endian(&$buf, $offset, $count)
{
    $r = 0;
    if (rb_is_little_endian())
    {
        for ($i = 0; $i < $count; $i++)
        {
            $r |= ord($buf['data'][$offset + $i]) << $i * 8;
        }
    }
    else
    {
        for ($i = 0; $i < $count; $i++)
        {
            $r |= ord($buf['data'][$offset + $count -1 - $i]) << $i * 8;
        }
    }
    return $r;
}

function rb_pack_base($format, $data, $offset, $count, &$buf)
{
    $bstr = pack($format, $data);
    for($i = 0; $i < $count; ++$i)
    {
        $buf['data'][$offset + $i] = $bstr[$i];
    }
}

function rb_unpack_base($format, &$buf, $offset, $count)
{
    $bstr = substr($buf['data'], $offset, $count);
    $data = unpack($format, $bstr);
    return $data[1];
}

function rb_get_bool(&$buf, $offset)
{
    return (bool) rb_get_uint8($buf, $offset);
}

function rb_get_int8(&$buf, $offset)
{
    return rb_unpack_base('c', $buf, $offset, sizeof_int8);
}

function rb_get_uint8(&$buf, $offset)
{
    return rb_unpack_base('C', $buf, $offset, sizeof_uint8);
}

function rb_get_int16(&$buf, $offset)
{
    $result = rb_read_little_endian($buf, $offset, sizeof_int16);
    $sign = $offset + (rb_is_little_endian() ? 1 : 0);
    $issigned = isset($buf['data'][$sign]) && ord($buf['data'][$sign]) & 0x80;
    // 65536 = 1 << 16 = Maximum unsigned 16-bit int
    return $issigned ? $result - 65536 : $result;
}

function rb_get_uint16(&$buf, $offset)
{
    return rb_unpack_base('v', $buf, $offset, sizeof_uint16);
}

function rb_get_int32(&$buf, $offset)
{
    $result = rb_read_little_endian($buf, $offset, sizeof_int32);

    $sign = $offset + (rb_is_little_endian() ? 3 : 0);
    $issigned = isset($buf['data'][$sign]) && ord($buf['data'][$sign]) & 0x80;

    if (PHP_INT_SIZE > 4)
    {
        // 4294967296 = 1 << 32 = Maximum unsigned 32-bit int
        return $issigned ? $result - 4294967296 : $result;
    }
    else
    {
        // 32bit / Windows treated number as signed integer.
        return $result;
    }
}

function rb_get_uint32(&$buf, $offset)
{
    return rb_unpack_base('V', $buf, $offset, sizeof_uint32);
}

function rb_get_int64(&$buf, $offset)
{
    return rb_read_little_endian($buf, $offset, sizeof_int64);
}

function rb_get_uint64(&$buf, $offset)
{
    return rb_read_little_endian($buf, $offset, sizeof_uint64);
}

function rb_get_float(&$buf, $offset)
{
    $value = rb_read_little_endian($buf, $offset, sizeof_float);
    $inthelper = pack("V", $value);
    $v = unpack("f", $inthelper);
    return $v[1];
}

function rb_get_double(&$buf, $offset)
{
    $value = rb_read_little_endian($buf, $offset, 4);
    $value2 = rb_read_little_endian($buf, $offset + 4, 4);
    $inthelper = pack("VV", $value, $value2);
    $v = unpack("d", $inthelper);
    return $v[1];
}

function rb_set_bool($data, $offset, &$buf)
{
    rb_set_uint8($data, $offset, $buf);
}

function rb_set_int8($data, $offset, &$buf)
{
    rb_pack_base('c', $data, $offset, sizeof_int8, $buf);
}

function rb_set_uint8($data, $offset, &$buf)
{
    rb_pack_base('C', $data, $offset, sizeof_uint8, $buf);
}

function rb_set_int16($data, $offset, &$buf)
{
    rb_write_little_endian($data, $offset, sizeof_int16, $buf);
}

function rb_set_uint16($data, $offset, &$buf)
{
    rb_pack_base('v', $data, $offset, sizeof_uint16, $buf);
}

function rb_set_int32($data, $offset, &$buf)
{
    rb_write_little_endian($data, $offset, sizeof_int32, $buf);
}

function rb_set_uint32($data, $offset, &$buf)
{
    rb_pack_base('V', $data, $offset, sizeof_uint32, $buf);
}

function rb_set_int64($data, $offset, &$buf)
{
    rb_write_little_endian($data, $offset, sizeof_int64, $buf);
}

function rb_set_uint64($data, $offset, &$buf)
{
    rb_write_little_endian($data, $offset, sizeof_uint64, $buf);
}

function rb_set_float($data, $offset, &$buf)
{
    $floathelper = pack("f", $data);
    $v = unpack("V", $floathelper);
    rb_write_little_endian($v[1], $offset, sizeof_float, $buf);
}

function rb_set_double($data, $offset, &$buf)
{
    $floathelper = pack("d", $data);
    $v = unpack("V*", $floathelper);
    rb_write_little_endian($v[1], $offset, 4, $buf);
    rb_write_little_endian($v[2], $offset + 4, 4, $buf);
}

function rb_get_rb_size(&$buf, $offset)
{
    return rb_get_uint32($buf, $offset);
}

function rb_get_rb_field_size(&$buf, $offset)
{
    return rb_get_uint8($buf, $offset);
}

function rb_get_rb_field_id(&$buf, $offset)
{
    return rb_get_rb_field_size($buf, $offset);
}

function rb_get_rb_offset(&$buf, $offset)
{
    return rb_get_rb_size($buf, $offset);
}

function rb_get_rb_buf_end(&$buf, $offset)
{
    return rb_get_uint32($buf, $offset);
}

function rb_set_rb_size($data, $offset, &$buf)
{
    rb_set_uint32($data, $offset, $buf);
}

function rb_set_rb_field_size($data, $offset, &$buf)
{
    rb_set_uint8($data, $offset, $buf);
}

function rb_set_rb_field_id($data, $offset, &$buf)
{
    rb_set_rb_field_size($data, $offset, $buf);
}

function rb_set_rb_offset($data, $offset, &$buf)
{
    rb_set_rb_size($data, $offset, $buf);
}

function rb_set_rb_buf_end($data, $offset, &$buf)
{
    rb_set_uint32($data, $offset, $buf);
}

function rb_set_string($data, $offset, $count, &$buf)
{
    $packer_type = 'a' . strval($count);
    rb_pack_base($packer_type, $data, $offset, $count, $buf);
}

function rb_get_string(&$buf, $offset, $count)
{
    $packer_type = 'a' . strval($count);
    $bstr = substr($buf['data'], $offset, $count);
    $data = unpack($packer_type, $bstr);
    return join('', $data);
}

function rb_seek_field_table_item($index)
{
    return rb_field_table_head_size + $index * rb_field_table_item_size;
}

function rb_create_buf($size)
{
    return array(
        "size"=> $size,
        "data"=> str_repeat("\0", $size),
        "start"=> 0,
        "pos"=> 0,
        "end"=> $size
    );
}

function rb_make_buf(&$data, $size)
{
    return array(
        'size'=> $size,
        'data'=> &$data,
        'start'=> 0,
        'pos'=> 0,
        'end'=> $size
    );
}

function rb_nested_buf(&$buf, $offset)
{
    $nested_buf = rb_create_buf(0);
    if (rb_check_buf($buf))
    {
        $nested_buf['data'] = &$buf['data'];
        $nested_buf['start'] = (0 == $offset) ? $buf['pos'] : ($buf['start'] + $offset);
        $nested_buf['end'] = $buf['end'];
        $nested_buf['pos'] = $nested_buf['start'];
        $nested_buf['size'] = $nested_buf['end'] - $nested_buf['start'];
    }
    return $nested_buf;
}

function rb_crc32(&$buf, $fields)
{
    $offset = rb_seek_field_table_item($fields);
    return crc32(substr($buf['data'], $buf['start'], $offset));
}

function rb_dump_buf($encode, &$obj_val, $size, $path)
{
    $buf = rb_create_buf($size);
    if (!$encode($obj_val, $buf))
    {
        return false;
    }
    $bytes = file_put_contents($path, $buf['data']);
    return $bytes == $size;
}

function rb_load_buf($path, $decode)
{
    $file_size = filesize($path);
    if ($file_size < 1)
    {
        return array(null, false);
    }
    $data = file_get_contents($path);
    $buf = rb_make_buf($data, $file_size);
    $size = rb_get_rb_size($buf, 0);
    if ($size < 1 || $size > $file_size)
    {
        return array(null, false);
    }
    return $decode($buf, 0);
}

function rb_check_buf(&$buf)
{
    return ($buf['size'] > 0) && ($buf['start'] <= $buf['pos']) && ($buf['pos'] <= $buf['end']) && ($buf['start'] + $buf['size'] <= $buf['end']);
}

function rb_encode_check(&$buf, $size)
{
    return rb_check_buf($buf) && ($buf['pos'] + $size < $buf['end']);
}

function rb_decode_check(&$buf, $offset, $size)
{
    return rb_check_buf($buf) && ($buf['start'] + $offset + $size < $buf['end']) && ($offset + $size < $buf['size']);
}

function rb_check_code(&$buf, $size, $fields)
{
    if (!rb_check_buf($buf))
    {
        return false;
    }
    if (($buf['start'] + $size > $buf['end']) || ($size > $buf['size']))
    {
        return false;
    }
    $pos = $buf['start'] + $size - sizeof_rb_buf_end;
    $end = rb_get_rb_buf_end($buf, $pos);
    $checkcode = rb_crc32($buf, $fields);
    if ($end != $checkcode)
    {
        return false;
    }
    return true;
}

function rb_set_buf_size($size, &$rb_val)
{
    if ($rb_val['start'] + sizeof_rb_size > $rb_val['end'])
    {
        return false;
    }
    rb_set_rb_size($size, $rb_val['start'], $rb_val);
    return true;
}

function rb_set_field_count($fields, &$rb_val)
{
    $head_size = rb_field_table_head_size;
    if ($rb_val['start'] + $head_size > $rb_val['end'])
    {
        return false;
    }
    $offset = $rb_val['start'] + $head_size - sizeof_rb_field_size;
    rb_set_rb_field_size($fields, $offset, $rb_val);
    $rb_val['pos'] = $rb_val['start'] + rb_seek_field_table_item($fields);
    if ($rb_val['pos'] > $rb_val['end'])
    {
        return false;
    }
    return true;
}

function rb_get_field_table_head(&$rb_val)
{
    $size = 0;
    $fields = 0;
    $offset = $rb_val['start'];
    if (($offset + rb_field_table_head_size) < $rb_val['end'])
    {
        $size = rb_get_rb_size($rb_val, $offset);
        $fields = rb_get_rb_field_size($rb_val, $offset + sizeof_rb_size);
    }
    return array($size, $fields);
}

function rb_set_field_table_item($index, $id, $offset, &$rb_val)
{
    $off = $rb_val['start'] + rb_seek_field_table_item($index);
    if ($off + rb_field_table_item_size > $rb_val['end'])
    {
        return false;
    }
    rb_set_rb_field_id($id, $off, $rb_val);
    rb_set_rb_offset($offset, $off + sizeof_rb_field_id, $rb_val);
    return true;
}

function rb_get_field_table_item($index, &$rb_val)
{
    $off = $rb_val['start'] + rb_seek_field_table_item($index);
    $size = rb_field_table_item_size;
    if ($off + $size > $rb_val['end'])
    {
        return array(0, 0, false);
    }
    $id = rb_get_rb_field_id($rb_val, $off);
    $offset = rb_get_rb_offset($rb_val, $off + sizeof_rb_field_id);
    return array($id, $offset, true);
}

function rb_encode_end($fields, &$rb_val)
{
    $size = sizeof_rb_buf_end;
    if (!rb_check_buf($rb_val) || ($rb_val['pos'] + $size > $rb_val['end']))
    {
        return false;
    }
    $end = rb_crc32($rb_val, $fields);
    rb_set_rb_buf_end($end, $rb_val['pos'], $rb_val);
    $rb_val['pos'] += $size;
    return true;
}

function rb_seek_array_table_item($index)
{
    return sizeof_rb_size + $index * sizeof_rb_offset;
}

function rb_set_array_count($size, &$rb_val)
{
    if (!rb_check_buf($rb_val))
    {
        return false;
    }
    if ($rb_val['pos'] + sizeof_rb_size > $rb_val['end'])
    {
        return false;
    }
    rb_set_rb_size($size, $rb_val['pos'], $rb_val);
    $rb_val['pos'] = $rb_val['start'] + rb_seek_array_table_item($size);
    if ($rb_val['pos'] > $rb_val['end'])
    {
        return false;
    }
    return true;
}

function rb_get_array_count(&$rb_val)
{
    $pos = $rb_val['start'];
    if ($pos + sizeof_rb_size < $rb_val['end'])
    {
        return rb_get_rb_size($rb_val, $pos);
    }
    return 0;
}

function rb_set_array_table_item($index, $offset, &$rb_val)
{
    $pos = $rb_val['start'] + rb_seek_array_table_item($index);
    if ($pos + sizeof_rb_offset > $rb_val['end'])
    {
        return false;
    }
    rb_set_rb_offset($offset, $pos, $rb_val);
    return true;
}

function rb_get_array_table_item($index, &$rb_val)
{
    $pos = $rb_val['start'] + rb_seek_array_table_item($index);
    if ($pos + sizeof_rb_offset > $rb_val['end'])
    {
        return array(0, false);
    }
    return array(rb_get_rb_offset($rb_val, $pos), true);
}

function rb_sizeof_string($obj_val)
{
    return sizeof_rb_size + strlen($obj_val);
}

function rb_encode_string($obj_val, &$rb_val)
{
    $size = strlen($obj_val);
    if (!rb_encode_check($rb_val, sizeof_rb_size + $size))
    {
        return false;
    }
    rb_set_rb_size($size, $rb_val['pos'], $rb_val);
    $rb_val['pos'] += sizeof_rb_size;
    if ($size > 0)
    {
        rb_set_string($obj_val, $rb_val['pos'], $size, $rb_val);
        $rb_val['pos'] += $size;
    }
    return true;
}

function rb_decode_string(&$rb_val, $offset)
{
    $size = sizeof_rb_size;
    if (!rb_decode_check($rb_val, $offset, $size))
    {
        return array(null, false);
    }
    $obj_len = rb_get_rb_size($rb_val, $rb_val['start'] + $offset);
    if ($obj_len > 0)
    {
        $off = $offset + $size;
        if (!rb_decode_check($rb_val, $off, $obj_len))
        {
            return array(null, false);
        }
        return array(rb_get_string($rb_val, $rb_val['start'] + $off, $obj_len), true);
    }
    return array('', true);
}

?>