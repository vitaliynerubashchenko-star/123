import os
import sqlite3
from flask import Flask, redirect, render_template_string, request, url_for

app = Flask(__name__)
UPLOAD_FOLDER = "images"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def get_db():
  conn = sqlite3.connect("crm.db")
  conn.row_factory = sqlite3.Row
  return conn


def init_db():
  conn = get_db()
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS apartments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            price TEXT,
            location TEXT,
            rooms TEXT,
            description TEXT,
            photo_paths TEXT,
            phone TEXT,
            realtor_name TEXT,
            realtor_phone TEXT
        )
    """)
  conn.commit()
  conn.close()


init_db()

# Адаптивный HTML-шаблон для ПК и телефонов
HTML_TEMPLATE = """
<!doctype html>
<html lang="uk">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>CRM Квартири</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<div class="container py-4">
    <h2 class="mb-4 text-center">📱 CRM Облік Квартир</h2>
    
    <div class="row">
        <!-- Форма добавления / редактирования -->
        <div class="col-md-5 mb-4">
            <div class="card p-3 shadow-sm">
                <h4>{{ 'Редагувати об\'єкт' if apt else 'Додати нову квартиру' }}</h4>
                <form method="POST" action="{{ url_for('update', id=apt['id']) if apt else url_for('add') }}" enctype="multipart/form-data">
                    <div class="mb-2">
                        <label class="form-label">Назва</label>
                        <input type="text" class="form-control" name="title" value="{{ apt['title'] if apt else '' }}" required>
                    </div>
                    <div class="mb-2">
                        <label class="form-label">Ціна</label>
                        <input type="text" class="form-control" name="price" value="{{ apt['price'] if apt else '' }}">
                    </div>
                    <div class="mb-2">
                        <label class="form-label">Локація</label>
                        <input type="text" class="form-control" name="location" value="{{ apt['location'] if apt else '' }}">
                    </div>
                    <div class="mb-2">
                        <label class="form-label">Кількість кімнат</label>
                        <input type="text" class="form-control" name="rooms" value="{{ apt['rooms'] if apt else '' }}">
                    </div>
                    <div class="mb-2">
                        <label class="form-label">Телефон власника</label>
                        <input type="text" class="form-control" name="phone" value="{{ apt['phone'] if apt else '' }}">
                    </div>
                    <div class="mb-2">
                        <label class="form-label">ПІБ ріелтора</label>
                        <input type="text" class="form-control" name="realtor_name" value="{{ apt['realtor_name'] if apt else '' }}">
                    </div>
                    <div class="mb-2">
                        <label class="form-label">Телефон ріелтора</label>
                        <input type="text" class="form-control" name="realtor_phone" value="{{ apt['realtor_phone'] if apt else '' }}">
                    </div>
                    <div class="mb-2">
                        <label class="form-label">Опис</label>
                        <textarea class="form-control" name="description" rows="3">{{ apt['description'] if apt else '' }}</textarea>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Фото (до 10 шт.)</label>
                        <input type="file" class="form-control" name="photos" multiple accept="image/*">
                    </div>
                    <button type="submit" class="btn btn-success w-100">{{ 'Зберегти зміни' if apt else 'Додати квартиру' }}</button>
                    {% if apt %}
                        <a href="{{ url_for('index') }}" class="btn btn-secondary w-100 mt-2">Скасувати</a>
                    {% endif %}
                </form>
            </div>
        </div>

        <!-- Список квартир -->
        <div class="col-md-7">
            <div class="card p-3 shadow-sm">
                <h4>Список об'єктів</h4>
                <div class="list-group">
                    {% for item in apartments %}
                        <div class="list-group-item list-group-item-action mb-2">
                            <div class="d-flex w-100 justify-content-between">
                                <h5 class="mb-1">{{ item['title'] }}</h5>
                                <span class="badge bg-primary rounded-pill">{{ item['price'] }}</span>
                            </div>
                            <p class="mb-1">📍 {{ item['location'] }} | Кімнат: {{ item['rooms'] }}</p>
                            <div class="btn-group btn-group-sm mt-2 flex-wrap">
                                <a href="{{ url_for('share', id=item['id']) }}" class="btn btn-outline-primary mb-1">📋 Текст презентації</a>
                                <a href="{{ url_for('edit', id=item['id']) }}" class="btn btn-outline-warning mb-1">✏️ Редагувати</a>
                                <a href="{{ url_for('delete', id=item['id']) }}" class="btn btn-outline-danger mb-1" onclick="return confirm('Видалити запис?')">🗑️ Видалити</a>
                            </div>
                        </div>
                    {% else %}
                        <p class="text-muted">База поки порожня.</p>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
</div>
</body>
</html>
"""


@app.route("/")
def index():
  conn = get_db()
  apartments = conn.execute("SELECT * FROM apartments").fetchall()
  conn.close()
  return render_template_string(HTML_TEMPLATE, apartments=apartments, apt=None)


@app.route("/add", methods=["POST"])
def add():
  title = request.form.get("title")
  price = request.form.get("price")
  location = request.form.get("location")
  rooms = request.form.get("rooms")
  description = request.form.get("description")
  phone = request.form.get("phone")
  realtor_name = request.form.get("realtor_name")
  realtor_phone = request.form.get("realtor_phone")

  photos = request.files.getlist("photos")
  photo_paths = []
  for photo in photos:
    if photo and photo.filename:
      filename = photo.filename
      path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
      photo.save(path)
      photo_paths.append(path)

  photos_str = ";".join(photo_paths)

  conn = get_db()
  conn.execute(
      """
        INSERT INTO apartments (title, price, location, rooms, description, photo_paths, phone, realtor_name, realtor_phone)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
      (
          title,
          price,
          location,
          rooms,
          description,
          photos_str,
          phone,
          realtor_name,
          realtor_phone,
      ),
  )
  conn.commit()
  conn.close()
  return redirect(url_for("index"))


@app.route("/edit/<int:id>")
def edit(id):
  conn = get_db()
  apt = conn.execute("SELECT * FROM apartments WHERE id = ?", (id,)).fetchone()
  apartments = conn.execute("SELECT * FROM apartments").fetchall()
  conn.close()
  return render_template_string(HTML_TEMPLATE, apartments=apartments, apt=apt)


@app.route("/update/<int:id>", methods=["POST"])
def update(id):
  title = request.form.get("title")
  price = request.form.get("price")
  location = request.form.get("location")
  rooms = request.form.get("rooms")
  description = request.form.get("description")
  phone = request.form.get("phone")
  realtor_name = request.form.get("realtor_name")
  realtor_phone = request.form.get("realtor_phone")

  conn = get_db()
  existing = conn.execute(
      "SELECT photo_paths FROM apartments WHERE id = ?", (id,)
  ).fetchone()
  photos_str = existing["photo_paths"] if existing else ""

  photos = request.files.getlist("photos")
  if photos and photos[0].filename:
    photo_paths = []
    for photo in photos:
      if photo and photo.filename:
        filename = photo.filename
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        photo.save(path)
        photo_paths.append(path)
    photos_str = ";".join(photo_paths)

  conn.execute(
      """
        UPDATE apartments SET title=?, price=?, location=?, rooms=?, description=?, photo_paths=?, phone=?, realtor_name=?, realtor_phone=?
        WHERE id=?
    """,
      (
          title,
          price,
          location,
          rooms,
          description,
          photos_str,
          phone,
          realtor_name,
          realtor_phone,
          id,
      ),
  )
  conn.commit()
  conn.close()
  return redirect(url_for("index"))


@app.route("/delete/<int:id>")
def delete(id):
  conn = get_db()
  conn.execute("DELETE FROM apartments WHERE id = ?", (id,))
  conn.commit()
  conn.close()
  return redirect(url_for("index"))


@app.route("/share/<int:id>")
def share(id):
  conn = get_db()
  apt = conn.execute("SELECT * FROM apartments WHERE id = ?", (id,)).fetchone()
  conn.close()
  if not apt:
    return "Об'єкт не знайдено"

  realtor_info = (
      f"\n📞 Ріелтор: {apt['realtor_name']} ({apt['realtor_phone']})"
      if apt["realtor_name"] or apt["realtor_phone"]
      else ""
  )
  text = (
      f"🏠 *{apt['title']}*\n📍 Локація: {apt['location']}\n🚪 Кімнат:"
      f" {apt['rooms']}\n💰 Ціна: *{apt['price']}*\n\n📝"
      f" Опис:\n{apt['description']}{realtor_info}\n\nЗвертайтесь для перегляду!"
  )

  return render_template_string(
      """
    <!doctype html>
    <html lang="uk">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Презентація</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light p-3">
        <div class="container card p-4 shadow-sm" style="max-width: 600px;">
            <h3>Текст презентації</h3>
            <p class="text-muted">Скопіюйте текст нижче для відправки:</p>
            <textarea class="form-control mb-3" rows="8" id="shareText">{{ text }}</textarea>
            <button class="btn btn-primary w-100 mb-2" onclick="copyText()">📋 Скопіювати текст</button>
            <a href="{{ url_for('index') }}" class="btn btn-secondary w-100">Назад до списку</a>
        </div>
        <script>
            function copyText() {
                var copyText = document.getElementById("shareText");
                copyText.select();
                copyText.setSelectionRange(0, 99999);
                navigator.clipboard.writeText(copyText.value);
                alert("Текст скопійовано в буфер обміну!");
            }
        </script>
    </body>
    </html>
    """,
      text=text,
  )


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug=True)