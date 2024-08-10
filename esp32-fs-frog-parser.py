### FSFROG reverse file structure

from struct import Struct
import heatshrink2
import sys
import os
import gzip

### 16 bytes in header
espfs_fs_header_t = Struct('<IBBHIHH')

### object header
espfs_object_header_t = Struct('<BBHHH')

### directory header 
### type, len, index, path_len, reserved
espfs_dir_header_t = Struct('<BBHHH')
### file header
### type, len, index, path_len, reserved, data_len, file_len, flags, compression, reserved
espfs_file_header_t = Struct('<BBHHHIIHBB')

### sort table
### offset
espfs_sorttable_entry_t = Struct('<I')

single = Struct('<B')


def read_object_entry(object_type, offset_point):

    entry = {}
    object_type = int.from_bytes(object_type)
    global parsed_object_count
    fp.seek(offset_point) ### reset offset point
    
    if(object_type == 1): ### dir
        read_size = 8
        obj_type, dir_len, index, path_len, reserved = espfs_dir_header_t.unpack(fp.read(read_size))
        path_parsed_name = (fp.read(path_len)).decode('utf-8').rstrip('\x00') ### remove byte padding
        entry = {"type" : obj_type, "index" : index, "path_len": path_len, "path" : path_parsed_name}
        if not (os.path.exists("result/" + path_parsed_name)):
            os.makedirs("result/" + path_parsed_name)
        print(entry)
        table.append(entry)
        parsed_object_count+=1
    else:
        read_size = 20 ### file
        obj_type, type_len, index, path_len, reserved, data_len, file_len, flags, compression, reserved = espfs_file_header_t.unpack(fp.read(read_size))
        path_parsed_name = (fp.read(path_len)).decode('utf-8').rstrip('\x00') ### remove byte padding
        entry = {"type" : obj_type, "index" : index, "path_len": path_len, "path" : path_parsed_name, "flags" : flags, "compression": compression, "data_len": data_len}
        print(entry)
        file_content = fp.read(file_len)
        if(compression == 1):
            file_content = heatshrink2.decompress(file_content)
        if(flags == 2):
            try:
                file_content = gzip.decompress(file_content)
            except Exception as e:
                pass
        fw = open("result/" + path_parsed_name, "wb")
        fw.write(file_content)
        fw.close()
        table.append(entry)
        parsed_object_count+=1
   
def parse_offsets(objNum):
    global offsets
    for i in range(objNum):
        offsets.append(espfs_sorttable_entry_t.unpack(fp.read(4))[0])
    print(max(offsets))

def main():
    fp = open("sample3.bin", "rb")
    magic, file_len, version_major, version_minor, binary_len, num_objects, reserved= espfs_fs_header_t.unpack(fp.read(16))
    parsed_object_count = 0
    accum_reader = 0
    table = []
    offsets = []

    if(magic == 726877765): ### efs+ file magic
        print("Magic: " + str(magic))
        print("header_len: " + str(file_len))
        print("bin_len:" + str(binary_len))
        print("num_objects:" + str(num_objects))
        data_offset = 16+(num_objects*8)
        fp.seek(data_offset)
        print("Offset: " + str(data_offset))

        parse_offsets(num_objects)
        
        for i in range(len(offsets)):
            fp.seek(offsets[i])
            read_object_entry(single.unpack(fp.read(1)), offsets[i])

    fp.close()
    
    
if __name__ == "__main__":
    main()
