"""Fill only the native Save As dialog owned by Power BI Desktop."""
import ctypes as c
from ctypes import wintypes as w
from pathlib import Path
import argparse, time, psutil

parser=argparse.ArgumentParser()
parser.add_argument('path')
parser.add_argument('--type',choices=['pbix','pbip'],default='pbix')
args=parser.parse_args()
target=Path(args.path).resolve()
root=Path(__file__).resolve().parents[1]
assert target.is_relative_to(root), 'Output must remain inside this workspace'
assert not target.exists(), 'Refusing to overwrite an existing file'
u=c.windll.user32
u.SetProcessDPIAware()
u.SendMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM];u.SendMessageW.restype=c.c_ssize_t
u.GetClassNameW.argtypes=[w.HWND,w.LPWSTR,c.c_int]
u.GetWindowTextW.argtypes=[w.HWND,w.LPWSTR,c.c_int]
u.GetWindowThreadProcessId.argtypes=[w.HWND,c.POINTER(w.DWORD)]
u.SetForegroundWindow.argtypes=[w.HWND]
u.GetWindowRect.argtypes=[w.HWND,c.POINTER(w.RECT)]
callback=c.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
def window_text(h):
    b=c.create_unicode_buffer(500);u.GetWindowTextW(h,b,len(b));return b.value
def classname(h):
    b=c.create_unicode_buffer(100);u.GetClassNameW(h,b,len(b));return b.value
dialogs=[]
@callback
def top(h,l):
    if window_text(h)=='Save As':
        pid=w.DWORD();u.GetWindowThreadProcessId(h,c.byref(pid))
        if psutil.Process(pid.value).name().lower()=='pbidesktop.exe':dialogs.append(h)
    return True
u.EnumWindows(top,0)
assert len(dialogs)==1, f'Expected one Power BI Save As dialog, got {len(dialogs)}'
dialog=dialogs[0];children=[]
@callback
def child(h,l):children.append(h);return True
u.EnumChildWindows(dialog,child,0)
edit=next(h for h in children if classname(h)=='Edit' and u.GetDlgCtrlID(h)==1001)
combo=next(h for h in children if classname(h)=='ComboBox' and 1<u.SendMessageW(h,0x146,0,0)<10)
button=next(h for h in children if classname(h)=='Button' and u.GetDlgCtrlID(h)==1)
options=[]
for i in range(u.SendMessageW(combo,0x146,0,0)):
    label=c.create_unicode_buffer(1000)
    u.SendMessageW(combo,0x148,i,c.cast(label,c.c_void_p).value)
    options.append(label.value)
desired=next(i for i,label in enumerate(options) if '*.'+args.type in label)
# Send keys directly to the native combobox rather than the global keyboard.
u.GetForegroundWindow.restype=w.HWND
u.keybd_event(0x12,0,0,0);u.keybd_event(0x12,0,2,0)
u.SetForegroundWindow(dialog)
time.sleep(.2)
fgpid=w.DWORD();u.GetWindowThreadProcessId(u.GetForegroundWindow(),c.byref(fgpid))
assert psutil.Process(fgpid.value).name().lower()=='pbidesktop.exe','Power BI must own foreground before input'
rect=w.RECT();u.GetWindowRect(combo,c.byref(rect))
assert u.SetCursorPos(rect.right-12,(rect.top+rect.bottom)//2)
u.mouse_event(2,0,0,0,0);u.mouse_event(4,0,0,0,0)
time.sleep(.2)
class COMBOBOXINFO(c.Structure):
    _fields_=[('cbSize',w.DWORD),('rcItem',w.RECT),('rcButton',w.RECT),('stateButton',w.DWORD),('hwndCombo',w.HWND),('hwndItem',w.HWND),('hwndList',w.HWND)]
info=COMBOBOXINFO();info.cbSize=c.sizeof(info)
u.GetComboBoxInfo.argtypes=[w.HWND,c.POINTER(COMBOBOXINFO)]
assert u.GetComboBoxInfo(combo,c.byref(info))
if not u.SendMessageW(combo,0x157,0,0):u.SendMessageW(combo,0x14F,1,0)
time.sleep(.15)
item=w.RECT()
assert u.SendMessageW(info.hwndList,0x198,desired,c.cast(c.pointer(item),c.c_void_p).value)!=-1
point=w.POINT(item.left+20,(item.top+item.bottom)//2)
u.ClientToScreen.argtypes=[w.HWND,c.POINTER(w.POINT)]
assert u.ClientToScreen(info.hwndList,c.byref(point))
assert u.SetCursorPos(point.x,point.y)
u.mouse_event(2,0,0,0,0);u.mouse_event(4,0,0,0,0)
time.sleep(.4)
assert u.SendMessageW(combo,0x147,0,0)==desired,options
u.SendMessageW(edit,0xB1,0,-1) # EM_SETSEL: select existing filename.
u.SendMessageW(edit,0x102,8,1) # WM_CHAR Backspace: raise normal edit notifications.
for char in str(target):u.SendMessageW(edit,0x102,ord(char),1)
time.sleep(.25)
readback=c.create_unicode_buffer(2000)
u.SendMessageW(edit,0xD,len(readback),c.cast(readback,c.c_void_p).value)
assert readback.value==str(target),readback.value
print('Filename verified. Format index:',u.SendMessageW(combo,0x147,0,0),flush=True)
u.SendMessageW(button,0xF5,0,0)
print('Save submitted:',target,flush=True)
