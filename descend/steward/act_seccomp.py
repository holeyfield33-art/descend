"""Minimal owned x86_64 seccomp filter; fail closed on any unsupported runtime."""
import ctypes
import errno
import platform
import sys


def install():
    if sys.platform != "linux" or platform.machine() != "x86_64":
        raise RuntimeError("Act syscall filter supports Linux x86_64 only")
    # Linux x86_64 syscall ABI, restricted to file IO, memory, clocks/signals,
    # identity queries and interpreter bookkeeping. Unknown syscalls deny.
    # Filesystem writes remain subject to read-only mounts / bounded tmpfs.
    allowed = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
               17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 32, 33, 35,
               36, 37, 38, 39, 60, 62, 63, 72, 73, 74, 75, 76, 77, 78, 79,
               80, 81, 82, 83, 84, 85, 87, 89, 90, 91, 92, 93, 94, 95,
               96, 97, 98, 99, 100, 102, 104, 107, 108, 110, 111, 115,
               118, 121, 124, 131, 132, 158, 186, 200, 201, 202, 217, 218,
               228, 229, 230, 231, 234, 235, 257, 258, 261, 262, 263, 264,
               267, 268, 269, 270, 271, 273, 274, 275, 280, 281, 285,
               291, 292, 293, 302, 316, 318, 332, 334, 437, 439, 441}
    class Filter(ctypes.Structure):
        _fields_ = [("code", ctypes.c_ushort), ("jt", ctypes.c_ubyte),
                    ("jf", ctypes.c_ubyte), ("k", ctypes.c_uint)]
    class Program(ctypes.Structure):
        _fields_ = [("len", ctypes.c_ushort), ("filter", ctypes.POINTER(Filter))]
    # BPF load arch, validate x86_64 (kill on mismatch), load syscall number.
    rules = [(0x20, 0, 0, 4), (0x15, 1, 0, 0xC000003E),
             (0x06, 0, 0, 0x80000000), (0x20, 0, 0, 0)]
    # x32 uses the same audit arch with syscall bit 30; deny that ABI outright.
    rules.extend([(0x45, 0, 1, 0x40000000), (0x06, 0, 0, 0x00050000 | errno.EPERM)])
    for number in sorted(allowed):
        rules.extend([(0x15, 0, 1, number), (0x06, 0, 0, 0x7FFF0000)])
    rules.append((0x06, 0, 0, 0x00050000 | errno.EPERM))
    filters = (Filter * len(rules))(*(Filter(*row) for row in rules))
    program = Program(len(rules), filters)
    libc = ctypes.CDLL(None, use_errno=True)
    libc.prctl.restype = ctypes.c_int
    if libc.prctl(38, 1, 0, 0, 0) != 0 or libc.prctl(22, 2, ctypes.byref(program), 0, 0) != 0:
        raise RuntimeError("Act syscall filter installation failed")


if __name__ == "__main__":
    install()
