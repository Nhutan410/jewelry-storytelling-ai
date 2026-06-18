# AI Storytelling Assistant

## Cấu hình `.env`

Tạo file `.env` từ `.env.example`:

```env
OPENAI_API_KEY=sk-your-openai-api-key
AUTH_USERNAME=your-username
AUTH_PASSWORD=your-password
```

Không commit `.env` lên GitHub.

## Chạy bằng Docker Compose

```bash
docker compose up --build
```

Mở app tại:

```text
http://localhost:8501
```

Nếu port `8501` đã bị chiếm, đổi mapping trong `docker-compose.yml`:

```yaml
ports:
  - "8502:8501"
```

Sau đó mở:

```text
http://localhost:8502
```

## Chạy bằng Docker CLI

Build image:

```bash
docker build -t storytelling:latest .
```

Chạy container:

```bash
docker run --rm --env-file .env --name storytelling -p 8501:8501 storytelling:latest
```

Nếu port `8501` đã bị chiếm:

```bash
docker run --rm --env-file .env --name storytelling -p 8502:8501 storytelling:latest
```

## Chạy local bằng Python

macOS/Linux:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Windows:

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
