import sys
path = r'c:/Users/yatyr/workspace/dwg2dxf/dwg2dxf/libdxfrw/src/intern/drw_textcodec.cpp'
f = open(path, 'rb')
d = f.read()
f.close()
old = b'k k k<end'
new = b'kk<end'
count = d.count(old)
print(f'Count: {count}')
if count > 0:
    d = d.replace(old, new)
    f = open(path, 'wb')
    f.write(d)
    f.close()
    print('Replaced')
else:
    print('Not found')
