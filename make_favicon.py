import struct, zlib, math

def png_chunk(chunk_type, data):
    c = chunk_type + data
    return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

def make_favicon_png(size=32):
    cx, cy = size / 2, size / 2
    pixels = []

    shield_pts = [(-0.72, -0.82), (0.72, -0.82), (0.72, 0.15), (0, 1.0), (-0.72, 0.15)]
    inner_pts  = [(-0.42, -0.52), (0.42, -0.52), (0.42, 0.05), (0, 0.68), (-0.42, 0.05)]

    def pip(px, py, pts):
        inside = False
        j = len(pts) - 1
        for i in range(len(pts)):
            xi, yi = pts[i]; xj, yj = pts[j]
            if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        return inside

    for y in range(size):
        row = []
        for x in range(size):
            nx = (x - cx + 0.5) / (size / 2)
            ny = (y - cy + 0.5) / (size / 2)

            if pip(nx, ny, shield_pts):
                if pip(nx, ny, inner_pts):
                    r, g, b, a = 26, 10, 10, 160
                else:
                    r, g, b, a = 255, 107, 43, 255

                dist = math.sqrt(nx * nx + (ny - 0.12) ** 2)
                if dist < 0.22:
                    if dist < 0.1:
                        r, g, b, a = 255, 107, 43, 255
                    else:
                        r, g, b, a = 255, 255, 255, 255
            else:
                r, g, b, a = 0, 0, 0, 0

            row.extend([r, g, b, a])
        pixels.append(row)

    raw = b''
    for row in pixels:
        raw += b'\x00' + bytes(row)

    compressed = zlib.compress(raw, 9)
    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = png_chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0))
    idat = png_chunk(b'IDAT', compressed)
    iend = png_chunk(b'IEND', b'')
    return sig + ihdr + idat + iend

with open('/home/ubuntu/webaudit/src/webaudit/static/favicon.png', 'wb') as f:
    f.write(make_favicon_png(32))

print('favicon.png created, size:', 32)
