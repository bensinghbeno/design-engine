import struct, sys
def bounds(fn):
    with open(fn,'rb') as f:
        f.read(80); n=struct.unpack('<I',f.read(4))[0]
        xs=[];ys=[];zs=[]
        for _ in range(n):
            f.read(12)
            for _v in range(3):
                x,y,z=struct.unpack('<3f',f.read(12)); xs.append(x);ys.append(y);zs.append(z)
            f.read(2)
    return (min(xs),max(xs),min(ys),max(ys),min(zs),max(zs))
for fn in ['arm.stl','connector.stl','crossbar.stl']:
    b=bounds(fn)
    print(fn, "raw", [round(v,3) for v in b])
    print("   scaled", [round(v*.1,3) for v in b])
    print("   center scaled", [round((b[0]+b[1])*.05,3),round((b[2]+b[3])*.05,3),round((b[4]+b[5])*.05,3)])
