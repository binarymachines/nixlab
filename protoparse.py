#!/usr/bin/env python

'''
Usage:
    protoparse --file <protofile>
'''

import os, sys
import json
import re
import docopt
from collections import namedtuple


protobuf_pkg_rx = re.compile(r'(package)[\s]+[a-zA-Z0-9]+[\s]?;')
protobuf_svc_rx = re.compile(r'(service)[\s]+[a-zA-Z0-9]+[\s]?\{')
protobuf_msg_rx = re.compile(r'(message)[\s]+[a-zA-Z0-9]+[\s]?\{')

protobuf_rpc_rx = re.compile(r'(rpc)(.*?);')
protobuf_return_stmt_rx = re.compile(r'(returns)(.*?);')
protobuf_func_name_rx = re.compile(r'(rpc)(.*?)\(')

paren_closure_rx = re.compile(r'\((.*?)\)')


FunctionDef = namedtuple('FunctionDef', 'name param_type return_type')


class ServiceDefinition(object):
    def __init__(self, name):
        self.name = name
        self.functions = list()

    def add_function(self, fdef: FunctionDef):
        self.functions.append(
            {
                'name': fdef.name,
                'param_type': fdef.param_type,
                'return_type': fdef.return_type
            }
        )

    def as_data(self):
        return {
            'service': self.name,
            'functions': self.functions 
        }
        

def get_package_name(protodef:str) -> str:

    pkg_def = None
    for expression in re.finditer(protobuf_pkg_rx, protodef):
        if pkg_def:
            raise Exception('your .proto file must have one and only one package definition.')
        else:
            pkg_def = expression.group()
    
    return pkg_def.split(' ')[1].rstrip(';')


def get_message_defs(protodef:str) -> str:

    msg_defs = []
    for expression in re.finditer(protobuf_msg_rx, protodef):
        tokens = expression.group().split(' ')
        for t in tokens:
            if not t:
                continue
            elif t == 'message':
                continue
            else:
                msg_defs.append(t.strip())
                break

    return msg_defs


def preprocess(protodef):

    pdlines = protodef.split('\n')
    
    linebuffer = []
    for raw_line in pdlines:
        line = raw_line.strip()
        if line.startswith('//'):
            continue
        elif not line:
            continue
        else:
            linebuffer.append(line)
    
    compact_protodef = '\n'.join(linebuffer)
    return str(compact_protodef)


def get_input_type_from_rpc_decl(decl):

    tokens = decl.split('returns')
    match = re.search(paren_closure_rx, tokens[0])
    raw_type = match.group()
    return raw_type.lstrip('(').rstrip(')')


def get_return_type_from_rpc_decl(decl):

    match = re.search(protobuf_return_stmt_rx, decl)
    return_stmt = match.group()
    open_idx = return_stmt.index('(')
    close_idx = return_stmt.index(')')
    return return_stmt[open_idx+1:close_idx]


def get_function_name_from_rpc_decl(decl):

    match = re.search(protobuf_func_name_rx, decl)    
    raw_name = match.group().lstrip('rpc').rstrip('(')
    return raw_name.strip()


def get_service_defs(raw_protodef:str):   

    protodef = preprocess(raw_protodef)

    service_defs = [] 
    for match in re.finditer('(service)', protodef, re.MULTILINE):        
        match_start = match.span()[0]
        match_end = match.span()[1]

        first_curly_index = protodef.index('{', match_end)
        
        service_name = protodef[match_end:first_curly_index].strip()

        service_defs.append(ServiceDefinition(service_name))

        # now get the body
        body = []
        index = first_curly_index + 1
        open_frames = 1
        while True:
            if protodef[index] == '{':
                open_frames += 1
            if protodef[index] == '}':
                open_frames -= 1
            if open_frames == 0:
                break
            index += 1

        raw_body = protodef[first_curly_index:index]

        for m in re.finditer(protobuf_rpc_rx, raw_body):
            rpc_decl = m.group()
            return_type = get_return_type_from_rpc_decl(rpc_decl)
            func_name = get_function_name_from_rpc_decl(rpc_decl)
            input_type = get_input_type_from_rpc_decl(rpc_decl)

            service_defs[-1].add_function(FunctionDef(name=func_name, param_type=input_type, return_type=return_type))

    return service_defs
        

def main(args):
    
    proto_filename = args['<protofile>']

    filedata = None
    with open(proto_filename) as f:
        filedata = f.read()

    pkg_name = get_package_name(preprocess(filedata))
    
    output = {
        pkg_name: [sd.as_data() for sd in get_service_defs(filedata)]
    }
    
    print(json.dumps(output))


if __name__ == '__main__':
    args = docopt.docopt(__doc__)
    main(args)