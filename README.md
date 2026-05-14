# hwp2hwpx

HWP(한글 워드프로세서) 파일을 HWPX(OWPML) 형식으로 변환하는 Python 패키지.

[neolord0/hwp2hwpx](https://github.com/neolord0/hwp2hwpx) Java 라이브러리를 번들하여
`pip install` 한 줄로 설치, 바로 사용할 수 있게 만든 래퍼입니다.

## 요구사항

- Python 3.8+
- Java Runtime Environment (JRE) 8+

## 설치

```bash
pip install hwp2hwpx
```

Java가 없으면:

```bash
# Windows
winget install EclipseAdoptium.Temurin.21.JDK

# macOS
brew install temurin

# Linux (Debian/Ubuntu)
apt install default-jre
```

## 사용법

### CLI

```bash
# 단일 파일
hwp2hwpx document.hwp

# 여러 파일
hwp2hwpx *.hwp

# 출력 디렉토리 지정
hwp2hwpx document.hwp -o output/

# 폴더 내 전체 변환 (재귀)
hwp2hwpx ./documents/ -r
```

### Python API

```python
from hwp2hwpx import convert, convert_batch

# 단일 파일
output_path = convert("document.hwp")
output_path = convert("document.hwp", "output.hwpx")

# 배치
results = convert_batch(["a.hwp", "b.hwp"], output_dir="output/")
for input_path, output_path, error in results:
    if error:
        print(f"FAIL: {input_path}: {error}")
    else:
        print(f"OK: {output_path}")
```

## 한글 경로 지원

Windows에서 한글(Korean) 파일 경로를 자동으로 처리합니다.
내부적으로 임시 ASCII 경로를 경유하여 JVM 인코딩 문제를 우회합니다.

## 라이선스

Apache License 2.0

원본 Java 라이브러리:
- [hwp2hwpx](https://github.com/neolord0/hwp2hwpx) by neolord0
- [hwplib](https://github.com/neolord0/hwplib) by neolord0
- [hwpxlib](https://github.com/neolord0/hwpxlib) by neolord0
