# AI Storytelling Assistant

Ứng dụng Streamlit giúp tư vấn viên PNJ chọn khách hàng, chọn sản phẩm và sinh câu chuyện trang sức cá nhân hóa bằng OpenAI.

## Tính năng chính

- Đăng nhập đơn giản bằng username/password từ `.env`.
- Xem dữ liệu khách hàng, persona và tín hiệu hành vi.
- Lọc danh mục sản phẩm PNJ theo tên, giới tính, loại sản phẩm và khoảng giá.
- Tự động chọn framework storytelling phù hợp.
- Sinh câu chuyện cá nhân hóa và tin nhắn Zalo bằng OpenAI.

## Yêu cầu

- Docker và Docker Compose, hoặc Python 3.10+ nếu chạy local.
- OpenAI API key.
- File dữ liệu trong thư mục `data/`:
  - `metadata.json`
  - `customer_data_poc_enhanced.xlsx`

## Cấu hình `.env`

Tạo file `.env` từ `.env.example` và điền giá trị thật:

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

Sau đó mở `http://localhost:8502`.

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

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Trên Windows:

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
