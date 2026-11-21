"""Small client for the user's already-running local Blender MCP endpoint."""
import socket,json,sys
def send(code,timeout=300):
    with socket.create_connection(('127.0.0.1',9876),10) as s:
        s.settimeout(timeout);s.sendall(json.dumps({'type':'execute_code','params':{'code':code}}).encode());buf=b''
        while True:
            piece=s.recv(65536)
            if not piece:break
            buf+=piece
            try:return json.loads(buf)
            except json.JSONDecodeError:pass
    return buf.decode(errors='replace')
if __name__=='__main__':
    if sys.argv[1]=='--file':code=open(sys.argv[2],encoding='utf-8').read()
    else:code=sys.argv[1]
    print(json.dumps(send(code),ensure_ascii=True))
