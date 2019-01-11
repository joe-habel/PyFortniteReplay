from glob import glob
import datetime
import struct


file_magic = b'\x7f\xe2\xa2\x1c'

def decode_int32(binary):
    return struct.unpack('<i', binary)[0]

def decode_uint32(binary):
    return struct.unpack('<I', binary)[0]

def decode_int64(binary):
    return struct.unpack('<q', binary)[0]

def decode_uint64(binary):
    return struct.unpack('<Q', binary)[0]


def fstring_reader(fileContent,pos):
    fname_len = fileContent[pos:pos+4]
    pos += 4
    fname_len = decode_int32(fname_len)
    if fname_len < 0:
        #print ('unic')
        fname_len = - fname_len
        return fileContent[pos:pos+fname_len*2].decode('utf-8',errors='replace').replace('\0','').strip(), pos+fname_len*2
    else:
        #print ('Nounic')
        return fileContent[pos:pos+fname_len].decode('utf-8',errors='ignore').replace('\0','').strip(), pos + fname_len
         

def read_replay(replay_file):
    file_magic = b'\x7f\xe2\xa2\x1c'
    eliminations = []
    elim_total = None
    position = None
    total_players = None
    with open(replay_file, 'rb') as rp:
        fileContent = rp.read()
    
    magic_number = fileContent[:4]
    
    if (magic_number != file_magic):
        print ('Invalid File')
    
    file_version = fileContent[4:8]
    
    length_ms = fileContent[8:12]
    game_length = decode_uint32(length_ms)/(100*60)
    
    network_version = fileContent[12:16]
    
    change_list = fileContent[16:20]
    
    friendly_name, pos = fstring_reader(fileContent,20)
    
    
    is_live = decode_uint32(fileContent[pos:pos+4]) != 0
    pos += 4
    
    if decode_uint32(file_version) >= 3:
        ## FIX THESE TICKS
        timestamp = fileContent[pos:pos+8]
        pos += 8
        timestamp = decode_int64(timestamp)
        date = datetime.datetime.fromtimestamp(timestamp/1e10)
    
    if decode_uint32(file_version) >= 2:
        is_compressed = decode_uint32(fileContent[pos:pos+4]) != 0
        pos += 4
    
    while pos < len(fileContent):
        chunk_type = decode_uint32(fileContent[pos:pos+4])
        pos += 4
        size_in_bytes = decode_int32(fileContent[pos:pos+4])
        pos += 4
        
        if chunk_type == 3:
            event_id, new_pos = fstring_reader(fileContent,pos)
            group, new_pos = fstring_reader(fileContent,new_pos)
            metadata, new_pos = fstring_reader(fileContent,new_pos)
            time1 = decode_uint32(fileContent[new_pos:new_pos+4])
            new_pos += 4
            time2 = decode_uint32(fileContent[new_pos:new_pos+4])
            new_pos += 4
            event_size = decode_uint32(fileContent[new_pos:new_pos+4])
            new_pos += 4 
            
            if group == 'playerElim':
                elim = {}
                new_pos += 45
                nick1, new_pos = fstring_reader(fileContent, new_pos)
                nick2, new_pos = fstring_reader(fileContent, new_pos)
                #print (nick1,nick2)
                try:
                    elim_type = str(fileContent[new_pos:new_pos+1])[-2:-1]
                except:
                    elim_type = 'NS'
                new_pos += 1
                knock_or_elim = decode_uint32(fileContent[new_pos:new_pos+4])
                elim['killed'] = nick1
                elim['killer'] = nick2
                elim['type'] = elim_type
                elim['knock_or_elim'] = knock_or_elim
                #print (elim_type,knock_or_elim)
                eliminations.append(elim)
            if metadata == 'AthenaMatchStats':
                new_pos += 12
                elim_total = decode_uint32(fileContent[new_pos:new_pos+4])

                
            if metadata == 'AthenaMatchTeamStats':
                new_pos += 4
                position = decode_uint32(fileContent[new_pos:new_pos+4])
                new_pos += 4
                total_players = decode_uint32(fileContent[new_pos:new_pos+4])

        pos += size_in_bytes
    return eliminations, elim_total, position, total_players

