# 1. 베이스 이미지 선택 (Playwright와 브라우저가 미리 설치된 공식 이미지 사용)
# 이 이미지를 사용하면 복잡한 의존성 문제를 한번에 해결할 수 있습니다.
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# 2. 환경 변수 설정
ENV PYTHONUNBUFFERED 1

# 3. 작업 디렉토리 설정 및 생성
WORKDIR /app

# 4. requirements.txt 파일을 먼저 복사하고 패키지 설치
# (이 순서로 해야 Docker 빌드 캐시를 효율적으로 사용할 수 있습니다)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 현재 폴더의 모든 소스 코드를 컨테이너의 /app 폴더로 복사
COPY . .

# 6. Playwright 브라우저 및 의존성 설치 (베이스 이미지에 포함되어 있지만, 확실하게 하기 위해 실행)
RUN playwright install --with-deps chromium

# 7. 컨테이너가 외부 요청을 받을 포트 설정
EXPOSE 8000

# 8. 컨테이너가 시작될 때 실행할 명령어
# 실제 운영 환경에서는 Gunicorn을 사용하는 것이 표준입니다.
CMD ["gunicorn", "--bind", "0.0.0.0:8000","--timeout", "120", "bucheonparking.wsgi:application"]