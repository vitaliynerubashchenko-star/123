import os
import shutil
import sqlite3
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk

# Створюємо папку для картинок, якщо її немає
if not os.path.exists("images"):
  os.makedirs("images")

# Ініціалізація бази даних
conn = sqlite3.connect("crm.db")
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

# Безпечне додавання нових колонок для старих баз даних
for col in [
    ("photo_paths", "TEXT"),
    ("phone", "TEXT"),
    ("realtor_name", "TEXT"),
    ("realtor_phone", "TEXT"),
]:
  try:
    cursor.execute(f"ALTER TABLE apartments ADD COLUMN {col[0]} {col[1]}")
    conn.commit()
  except sqlite3.OperationalError:
    pass


class CRMApp:

  def __init__(self, root):
    self.root = root
    self.root.title("CRM Квартири")
    self.root.geometry("1150x700")

    self.current_photos = []
    self.photo_index = 0
    self.editing_id = None

    # Ліва панель (Список)
    self.list_frame = tk.Frame(root)
    self.list_frame.pack(
        side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10
    )

    self.tree = ttk.Treeview(
        self.list_frame,
        columns=("ID", "Назва", "Ціна", "Ріелтор"),
        show="headings",
    )
    self.tree.heading("ID", text="ID")
    self.tree.heading("Назва", text="Назва")
    self.tree.heading("Ціна", text="Ціна")
    self.tree.heading("Ріелтор", text="Ріелтор")
    self.tree.column("ID", width=30)
    self.tree.pack(fill=tk.BOTH, expand=True)

    # Права панель (Форма, кнопки та перегляд фото)
    self.right_frame = tk.Frame(root)
    self.right_frame.pack(
        side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10
    )

    self.inputs = {}
    field_labels = [
        "Назва",
        "Ціна",
        "Локація",
        "Кімнати",
        "Телефон власника",
        "ПІБ ріелтора",
        "Телефон ріелтора",
    ]
    for label in field_labels:
      tk.Label(self.right_frame, text=f"{label}:").pack(anchor="w")
      entry = tk.Entry(self.right_frame, width=35)
      entry.pack(fill="x", pady=1)
      self.inputs[label] = entry

    tk.Label(self.right_frame, text="Опис:").pack(anchor="w")
    self.text_desc = tk.Text(self.right_frame, height=3, width=35)
    self.text_desc.pack(fill="x", pady=1)

    # Блок управління фото
    photo_btn_frame = tk.Frame(self.right_frame)
    photo_btn_frame.pack(fill="x", pady=2)

    tk.Button(
        photo_btn_frame,
        text="Додати фото (+)",
        command=self.add_photo,
        bg="#009688",
        fg="white",
    ).pack(side=tk.LEFT, expand=True, fill="x", padx=2)
    tk.Button(
        photo_btn_frame,
        text="Очистити фото",
        command=self.clear_photos,
        bg="#E91E63",
        fg="white",
    ).pack(side=tk.LEFT, expand=True, fill="x", padx=2)

    # Прев'ю фото та навігація
    self.image_label = tk.Label(
        self.right_frame, text="Фото відсутні", bg="#e0e0e0", width=30, height=6
    )
    self.image_label.pack(pady=2)

    nav_frame = tk.Frame(self.right_frame)
    nav_frame.pack(fill="x", pady=2)
    tk.Button(
        nav_frame, text="◀ Попереднє", command=self.prev_photo
    ).pack(side=tk.LEFT, expand=True, fill="x")
    self.photo_counter_label = tk.Label(nav_frame, text="0/0")
    self.photo_counter_label.pack(side=tk.LEFT, padx=5)
    tk.Button(nav_frame, text="Наступне ▶", command=self.next_photo).pack(
        side=tk.LEFT, expand=True, fill="x"
    )

    # Кнопки управління записами
    tk.Button(
        self.right_frame,
        text="Додати нову квартиру",
        command=self.add_apartment,
        bg="#4CAF50",
        fg="white",
    ).pack(fill="x", pady=2)
    tk.Button(
        self.right_frame,
        text="Редагувати (Завантажити у форму)",
        command=self.load_for_editing,
        bg="#FF9800",
        fg="white",
    ).pack(fill="x", pady=2)
    tk.Button(
        self.right_frame,
        text="Зберегти зміни",
        command=self.save_updated_apartment,
        bg="#8BC34A",
        fg="white",
    ).pack(fill="x", pady=2)
    tk.Button(
        self.right_frame,
        text="Видалити запис",
        command=self.delete_apartment,
        bg="#F44336",
        fg="white",
    ).pack(fill="x", pady=2)
    tk.Button(
        self.right_frame,
        text="Копіювати текст для месенджера",
        command=self.share_apartment,
        bg="#2196F3",
        fg="white",
    ).pack(fill="x", pady=2)

    self.load_data()

  def add_photo(self):
    if len(self.current_photos) >= 10:
      messagebox.showwarning(
          "Увага", "Можна додати максимум 10 фотографій до однієї квартири!"
      )
      return

    file_path = filedialog.askopenfilename(
        filetypes=[("Image files", "*.jpg *.png *.jpeg")]
    )
    if file_path:
      filename = os.path.basename(file_path)
      dest_path = os.path.join("images", filename)
      shutil.copy(file_path, dest_path)

      self.current_photos.append(dest_path)
      self.photo_index = len(self.current_photos) - 1
      self.update_image_display()

  def clear_photos(self):
    self.current_photos = []
    self.photo_index = 0
    self.update_image_display()

  def prev_photo(self):
    if self.current_photos:
      self.photo_index = (self.photo_index - 1) % len(self.current_photos)
      self.update_image_display()

  def next_photo(self):
    if self.current_photos:
      self.photo_index = (self.photo_index + 1) % len(self.current_photos)
      self.update_image_display()

  def update_image_display(self):
    if not self.current_photos:
      self.image_label.config(image="", text="Фото відсутні")
      self.photo_counter_label.config(text="0/0")
      return

    path = self.current_photos[self.photo_index]
    if os.path.exists(path):
      try:
        img = Image.open(path)
        img = img.resize((140, 90))
        self.photo_img = ImageTk.PhotoImage(img)
        self.image_label.config(image=self.photo_img, text="")
        self.photo_counter_label.config(
            text=f"{self.photo_index + 1}/{len(self.current_photos)}"
        )
      except Exception:
        self.image_label.config(image="", text="Помилка завантаження")
    else:
      self.image_label.config(image="", text="Файл не знайдено")

  def load_data(self):
    for row in self.tree.get_children():
      self.tree.delete(row)
    cursor.execute("SELECT id, title, price, realtor_name FROM apartments")
    for row in cursor.fetchall():
      self.tree.insert("", tk.END, values=row)

  def get_form_values(self):
    vals = [
        self.inputs[k].get()
        for k in [
            "Назва",
            "Ціна",
            "Локація",
            "Кімнати",
            "Телефон власника",
            "ПІБ ріелтора",
            "Телефон ріелтора",
        ]
    ]
    desc = self.text_desc.get("1.0", tk.END).strip()
    return vals, desc

  def add_apartment(self):
    vals, desc = self.get_form_values()
    if not vals[0]:
      messagebox.showerror("Помилка", "Введіть назву квартири!")
      return

    photos_str = ";".join(self.current_photos)

    cursor.execute(
        """INSERT INTO apartments (title, price, location, rooms, description, photo_paths, phone, realtor_name, realtor_phone) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            vals[0],
            vals[1],
            vals[2],
            vals[3],
            desc,
            photos_str,
            vals[4],
            vals[5],
            vals[6],
        ),
    )
    conn.commit()
    self.load_data()
    messagebox.showinfo("Успіх", "Квартиру додано до бази!")
    self.clear_form()

  def load_for_editing(self):
    selected = self.tree.selection()
    if not selected:
      messagebox.showwarning(
          "Увага", "Виберіть квартиру зі списку для редагування!"
      )
      return

    self.editing_id = self.tree.item(selected)["values"][0]
    cursor.execute(
        """SELECT title, price, location, rooms, description, photo_paths, phone, realtor_name, realtor_phone 
                   FROM apartments WHERE id = ?""",
        (self.editing_id,),
    )
    row = cursor.fetchone()
    if row:
      for entry in self.inputs.values():
        entry.delete(0, tk.END)

      self.inputs["Назва"].insert(0, row[0] or "")
      self.inputs["Ціна"].insert(0, row[1] or "")
      self.inputs["Локація"].insert(0, row[2] or "")
      self.inputs["Кімнати"].insert(0, row[3] or "")
      self.inputs["Телефон власника"].insert(0, row[6] or "")
      self.inputs["ПІБ ріелтора"].insert(0, row[7] or "")
      self.inputs["Телефон ріелтора"].insert(0, row[8] or "")

      self.text_desc.delete("1.0", tk.END)
      self.text_desc.insert("1.0", row[4] or "")

      photos_str = row[5] or ""
      self.current_photos = photos_str.split(";") if photos_str else []
      self.photo_index = 0
      self.update_image_display()

      messagebox.showinfo(
          "Редагування",
          f"Дані квартири ID {self.editing_id} завантажено. Внесіть зміни та"
          " натисніть «Зберегти зміни».",
      )

  def save_updated_apartment(self):
    if not self.editing_id:
      messagebox.showwarning(
          "Увага",
          "Спочатку виберіть запис і натисніть «Редагувати», щоб змінити його!",
      )
      return

    vals, desc = self.get_form_values()
    photos_str = ";".join(self.current_photos)

    cursor.execute(
        """UPDATE apartments SET title=?, price=?, location=?, rooms=?, 
                   description=?, photo_paths=?, phone=?, realtor_name=?, realtor_phone=? WHERE id=?""",
        (
            vals[0],
            vals[1],
            vals[2],
            vals[3],
            desc,
            photos_str,
            vals[4],
            vals[5],
            vals[6],
            self.editing_id,
        ),
    )
    conn.commit()
    self.load_data()
    messagebox.showinfo(
        "Успіх", f"Зміни для квартири ID {self.editing_id} успішно збережено!"
    )
    self.clear_form()
    self.editing_id = None

  def delete_apartment(self):
    selected = self.tree.selection()
    if not selected:
      messagebox.showwarning("Увага", "Виберіть квартиру для видалення!")
      return

    del_id = self.tree.item(selected)["values"][0]
    if messagebox.askyesno(
        "Підтвердження", f"Ви дійсно хочете видалити квартиру ID {del_id}?"
    ):
      cursor.execute("DELETE FROM apartments WHERE id = ?", (del_id,))
      conn.commit()
      self.load_data()
      self.clear_form()
      self.editing_id = None
      messagebox.showinfo("Успіх", "Запис видалено!")

  def clear_form(self):
    for entry in self.inputs.values():
      entry.delete(0, tk.END)
    self.text_desc.delete("1.0", tk.END)
    self.clear_photos()

  def share_apartment(self):
    selected = self.tree.selection()
    if not selected:
      messagebox.showwarning("Увага", "Виберіть квартиру для презентації!")
      return

    sel_id = self.tree.item(selected)["values"][0]
    cursor.execute(
        "SELECT title, price, location, rooms, description, realtor_name,"
        " realtor_phone FROM apartments WHERE id = ?",
        (sel_id,),
    )
    row = cursor.fetchone()
    if row:
      realtor_info = (
          f"\n📞 Ріелтор: {row[5]} ({row[6]})"
          if row[5] or row[6]
          else ""
      )
      text = (
          f"🏠 *{row[0]}*\n📍 Локація: {row[2]}\n🚪 Кімнат: {row[3]}\n💰"
          f" Ціна: *{row[1]}*\n\n📝 Опис:\n{row[4]}{realtor_info}\n\nЗвертайтесь"
          " для перегляду!"
      )
      self.root.clipboard_clear()
      self.root.clipboard_append(text)

      if os.path.exists("images"):
        os.system(f'explorer "{os.path.abspath("images")}"')

      messagebox.showinfo(
          "Готово",
          "Текст скопійовано в буфер обміну (з контактами ріелтора)!\nПапка з"
          " фотографіями відкрилася — перетягніть потрібні фото у чат.",
      )


if __name__ == "__main__":
  root = tk.Tk()
  app = CRMApp(root)
  root.mainloop()