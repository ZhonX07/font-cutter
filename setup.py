import PyInstaller.__main__
import os
import sys

font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "HMOSSSC.ttf")
if not os.path.exists(font_path):
    print(f"错误: 找不到字体文件 {font_path}")
    sys.exit(1)
PyInstaller.__main__.run([
    'fontsfileeditor.py',
    '--name=字体裁剪工具',
    '--onefile',
    '--windowed',
    '--add-data=HMOSSSC.ttf;.',
    '--clean',
])

print("打包完成！可执行文件位于 dist 文件夹中。")
