"""Set and verify a file path in the Open dialog owned by Power BI Desktop."""
import ctypes as c
from ctypes import wintypes as w
from pathlib import Path
import sys
import psutil

target=Path(sys.argv[1]).resolve()
assert target.is_file() and target.is_relative_to(Path(__file__).resolve().parents[1])
u=c.windll.user32
u.SendMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM]
u.SendMessageW.restype=c.c_ssize_t
u.GetWindowTextW.argtypes=[w.HWND,w.LPWSTR,c.c_int]
u.GetClassNameW.argtypes=[w.HWND,w.LPWSTR,c.c_int]
u.GetWindowThreadProcessId.argtypes=[w.HWND,c.POINTER(w.DWORD)]
callback=c.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
def text(h):
    b=c.create_unicode_buffer(2048);u.GetWindowTextW(h,b,len(b));return b.value
dialogs=[]
@callback
def top(h,l):
    if text(h)=='Open':
        pid=w.DWORD();u.GetWindowThreadProcessId(h,c.byref(pid))
        if psutil.Process(pid.value).name().lower()=='pbidesktop.exe':dialogs.append(h)
    return True
u.EnumWindows(top,0)
assert len(dialogs)==1,dialogs
children=[]
@callback
def child(h,l):children.append(h);return True
u.EnumChildWindows(dialogs[0],child,0)
def cls(h):
    b=c.create_unicode_buffer(100);u.GetClassNameW(h,b,100);return b.value
edit=next(h for h in children if cls(h)=='Edit' and u.GetDlgCtrlID(h)==1148)
button=next(h for h in children if cls(h)=='Button' and u.GetDlgCtrlID(h)==1)
u.SendMessageW(edit,0xB1,0,-1)
u.SendMessageW(edit,0x102,8,1)
for char in str(target):u.SendMessageW(edit,0x102,ord(char),1)
readback=c.create_unicode_buffer(2048)
u.SendMessageW(edit,0xD,len(readback),c.cast(readback,c.c_void_p).value)
assert readback.value==str(target),readback.value
u.SendMessageW(button,0xF5,0,0)
print('Verified filename and submitted:',target.name)
