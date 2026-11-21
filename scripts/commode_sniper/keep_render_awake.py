"""Temporarily inhibit automatic PC sleep until this render queue exits."""
import ctypes
import json
import sys
import time
from pathlib import Path

kernel=ctypes.WinDLL('kernel32',use_last_error=True)
kernel.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong]
kernel.OpenProcess.restype=ctypes.c_void_p
kernel.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_ulong]
kernel.CloseHandle.argtypes=[ctypes.c_void_p]
status=Path(__file__).resolve().parents[2]/'renders/commode_sniper/three_1080p_queue.json'
record=json.loads(status.read_text())
assert record['state']=='running'
process=kernel.OpenProcess(0x00100000,False,record['pid'])
if not process:
    raise OSError(ctypes.get_last_error(),'Cannot watch the render queue')
try:
    if not kernel.SetThreadExecutionState(0x80000001):
        raise OSError('Cannot temporarily prevent automatic sleep')
    print('Automatic sleep inhibited while render queue runs; display may sleep.',flush=True)
    result=kernel.WaitForSingleObject(process,0xFFFFFFFF)
    if result!=0:
        raise OSError('Render queue wait failed: '+str(result))
finally:
    kernel.SetThreadExecutionState(0x80000000)
    kernel.CloseHandle(process)
    print('Render queue exited; automatic sleep restored.',flush=True)
