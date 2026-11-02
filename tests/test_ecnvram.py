"""Run: python3 tests/test_ecnvram.py   (no Chromebook needed)"""
import importlib.machinery, importlib.util, os
path = os.path.join(os.path.dirname(__file__), "..", "rootfs", "overlay", "usr", "local", "sbin", "fleet-ec-nvram")
spec = importlib.util.spec_from_loader("ecn", importlib.machinery.SourceFileLoader("ecn", path))
ecn = importlib.util.module_from_spec(spec); spec.loader.exec_module(ecn)
assert ecn.crc8(bytes(15)) == 0 and ecn.crc8(b"\x01") == 0x07 and ecn.crc8(b"123456789") == 0xF4     # standard CRC-8 (poly 0x07)
block = bytearray(16); block[0] = 0x40; block[4] = 0x02; block[15] = ecn.crc8(bytes(block[:15])); block = bytes(block)
on = ecn.with_usb(block, True)
assert on[4] == 0x01 and on[15] == ecn.crc8(on[:15]) and on[0] == 0x40          # USB on, signed-only off, checksum right
assert ecn.with_usb(on, True) == on                                              # idempotent
off = ecn.with_usb(on, False)
assert off[4] == 0x00 and off[15] == ecn.crc8(off[:15])
other = bytearray(on); other[4] |= 0x04; other = bytes(other)                    # other developer flags stay untouched
assert ecn.with_usb(other, False)[4] == 0x04
print("ecnvram: OK")