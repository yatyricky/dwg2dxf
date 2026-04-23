path = r'c:/Users/yatyr/workspace/dwg2dxf/dwg2dxf/libdxfrw/src/intern/drw_textcodec.cpp'
with open(path, 'r', encoding='gb2312') as f:
    content = f.read()

# Fix 1: k k k<end -> k k<end
old1 = 'for (int k=sta; k k k<end; k++){'
new1 = 'for (int k=sta; k k<end; k++){'
if old1 in content:
    content = content.replace(old1, new1)
    print('Fixed k k k<end')
else:
    print('k k k<end not found')

# Fix 2: DRW_Conv932Table::toUtf8 boundary check
old2 = '''        } else {//2 bytes
            ++it;
            int code = (c << 8) | (unsigned char )(*it);'''
new2 = '''        } else {//2 bytes
            if (it + 1 < s->end()) {
                ++it;
                int code = (c << 8) | (unsigned char )(*it);'''
if old2 in content:
    content = content.replace(old2, new2)
    print('Fixed DRW_Conv932Table::toUtf8 boundary')
else:
    print('DRW_Conv932Table::toUtf8 boundary pattern not found')

with open(path, 'w', encoding='gb2312') as f:
    f.write(content)
print('Done')
