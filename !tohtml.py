# ppm_to_html.py
import sys
from PIL import Image
import base64
from io import BytesIO

def ppm_to_html(input_file, output_file):
    # 画像を読み込む（P3/P6両対応）
    img = Image.open(input_file)

    # バッファにPNG形式で保存
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    b64_data = base64.b64encode(buffer.getvalue()).decode()

    # HTML生成
    html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>PPM変換画像</title>
</head>
<body>
<img src="data:image/png;base64,{b64_data}" alt="PPM画像">
</body>
</html>"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"{output_file} にHTMLとして変換完了！")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("使い方: python ppm_to_html.py input.ppm output.html")
        sys.exit(1)

    ppm_to_html(sys.argv[1], sys.argv[2])
