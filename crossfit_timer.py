import tkinter as tk
from tkinter import messagebox
import time

class CrossfitTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("CrossFit Timer: Подтягивания/Отжимания/Приседания")
        self.root.geometry("500x500")
        self.root.resizable(False, False)

        # Переменные таймера
        self.running = False
        self.paused = False
        self.countdown_mode = False  # False = секундомер от 0, True = обратный отсчёт
        self.start_time = 0
        self.elapsed_time = 0  # в секундах
        self.target_time = 0   # для обратного отсчёта (в секундах)

        # Счётчик повторений
        self.rep_counter = 0

        # === Элементы интерфейса ===

        # Отображение времени
        self.time_label = tk.Label(root, text="00:00:00", font=("Helvetica", 48), fg="blue")
        self.time_label.pack(pady=20)

        # Кнопки управления таймером
        frame_buttons = tk.Frame(root)
        frame_buttons.pack(pady=10)

        self.start_btn = tk.Button(frame_buttons, text="Старт (с 0)", command=self.start_from_zero, width=12)
        self.start_btn.grid(row=0, column=0, padx=5)

        self.start_countdown_btn = tk.Button(frame_buttons, text="Обратный отсчёт", command=self.set_countdown, width=15)
        self.start_countdown_btn.grid(row=0, column=1, padx=5)

        self.pause_btn = tk.Button(frame_buttons, text="Пауза", command=self.pause, width=8, state=tk.DISABLED)
        self.pause_btn.grid(row=0, column=2, padx=5)

        self.stop_btn = tk.Button(frame_buttons, text="Стоп", command=self.stop, width=8)
        self.stop_btn.grid(row=0, column=3, padx=5)

        self.reset_btn = tk.Button(frame_buttons, text="Сбросить", command=self.reset, width=8)
        self.reset_btn.grid(row=0, column=4, padx=5)

        # Панель для настройки обратного отсчёта
        frame_countdown = tk.Frame(root)
        frame_countdown.pack(pady=10)

        tk.Label(frame_countdown, text="Установить время (ЧЧ:ММ:СС):").pack(side=tk.LEFT, padx=5)
        self.time_entry = tk.Entry(frame_countdown, width=10)
        self.time_entry.pack(side=tk.LEFT, padx=5)
        self.time_entry.insert(0, "00:01:00")  # пример: 1 минута

        self.set_btn = tk.Button(frame_countdown, text="Установить", command=self.set_custom_time)
        self.set_btn.pack(side=tk.LEFT, padx=5)

        # Счётчик повторений
        frame_counter = tk.Frame(root)
        frame_counter.pack(pady=20)

        tk.Label(frame_counter, text="Счётчик повторений (Enter):", font=("Helvetica", 12)).pack()
        self.counter_label = tk.Label(frame_counter, text="0", font=("Helvetica", 32), fg="green")
        self.counter_label.pack()

        self.reset_counter_btn = tk.Button(frame_counter, text="Сбросить счётчик", command=self.reset_counter)
        self.reset_counter_btn.pack(pady=5)

        # Подсказка по клавишам
        tk.Label(root, text="Нажмите Enter для +1 повторение", fg="gray", font=("Helvetica", 10)).pack(side=tk.BOTTOM, pady=10)
        tk.Label(root, text="Пробел — Пауза/Возобновить", fg="gray", font=("Helvetica", 10)).pack(side=tk.BOTTOM)

        # Привязка клавиш
        self.root.bind('<Return>', self.increment_counter)
        self.root.bind('<space>', self.toggle_pause_space)

        # Обновление таймера
        self.update_timer()

    # ---------- Логика таймера ----------
    def start_from_zero(self):
        """Секундомер с нуля"""
        if self.running and not self.paused:
            return
        self.countdown_mode = False
        self.elapsed_time = 0
        self.running = True
        self.paused = False
        self.start_time = time.time() - self.elapsed_time
        self._enable_pause_stop()
        self.start_btn.config(state=tk.DISABLED)
        self.start_countdown_btn.config(state=tk.DISABLED)

    def set_countdown(self):
        """Запуск обратного отсчёта с установленного времени"""
        try:
            # Парсим время из поля ввода
            t_str = self.time_entry.get()
            h, m, s = map(int, t_str.split(':'))
            total_seconds = h * 3600 + m * 60 + s
            if total_seconds <= 0:
                raise ValueError
        except:
            messagebox.showerror("Ошибка", "Введите время в формате ЧЧ:ММ:СС (например, 00:05:00)")
            return

        if self.running and not self.paused:
            return

        self.countdown_mode = True
        self.target_time = total_seconds
        self.elapsed_time = total_seconds  # текущее оставшееся время
        self.running = True
        self.paused = False
        self.start_time = time.time()
        self._enable_pause_stop()
        self.start_btn.config(state=tk.DISABLED)
        self.start_countdown_btn.config(state=tk.DISABLED)

    def set_custom_time(self):
        """Установить время для обратного отсчёта (без запуска)"""
        if self.running:
            return
        try:
            t_str = self.time_entry.get()
            h, m, s = map(int, t_str.split(':'))
            total = h * 3600 + m * 60 + s
            if total < 0:
                raise ValueError
            self.countdown_mode = True
            self.elapsed_time = total
            self.target_time = total
            self._update_display(total)
        except:
            messagebox.showerror("Ошибка", "Неверный формат. Используйте ЧЧ:ММ:СС")

    def pause(self):
        if self.running and not self.paused:
            self.paused = True
            self.pause_btn.config(text="Возобновить")
            # зафиксируем текущее время
            if self.countdown_mode:
                self.elapsed_time = max(0, self.target_time - (time.time() - self.start_time))
            else:
                self.elapsed_time = time.time() - self.start_time
        elif self.running and self.paused:
            self.paused = False
            self.pause_btn.config(text="Пауза")
            self.start_time = time.time() - self.elapsed_time
        self._enable_pause_stop()

    def toggle_pause_space(self, event=None):
        if self.running:
            self.pause()

    def stop(self):
        self.running = False
        self.paused = False
        self.pause_btn.config(text="Пауза", state=tk.DISABLED)
        self.start_btn.config(state=tk.NORMAL)
        self.start_countdown_btn.config(state=tk.NORMAL)

    def reset(self):
        self.running = False
        self.paused = False
        self.countdown_mode = False
        self.elapsed_time = 0
        self.target_time = 0
        self._update_display(0)
        self.pause_btn.config(text="Пауза", state=tk.DISABLED)
        self.start_btn.config(state=tk.NORMAL)
        self.start_countdown_btn.config(state=tk.NORMAL)

    def _enable_pause_stop(self):
        self.pause_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.NORMAL)

    def _update_display(self, seconds):
        """Обновить текстовое отображение времени"""
        if seconds < 0:
            seconds = 0
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        self.time_label.config(text=f"{h:02d}:{m:02d}:{s:02d}")

    def update_timer(self):
        """Вызывается каждые 100 мс для обновления таймера"""
        if self.running and not self.paused:
            current = time.time()
            if self.countdown_mode:
                remaining = self.target_time - (current - self.start_time)
                if remaining <= 0:
                    # Время вышло
                    self._update_display(0)
                    self.stop()
                    messagebox.showinfo("Таймер", "Время вышло!")
                else:
                    self._update_display(remaining)
            else:
                elapsed = current - self.start_time
                self._update_display(elapsed)
        elif self.running and self.paused:
            # Показываем замороженное значение
            if self.countdown_mode:
                self._update_display(self.elapsed_time)
            else:
                self._update_display(self.elapsed_time)
        elif not self.running:
            # Если сброшено, показываем 0 или установленное время
            if self.countdown_mode and not self.running and self.elapsed_time > 0:
                self._update_display(self.elapsed_time)
            else:
                if not self.countdown_mode or (self.countdown_mode and self.elapsed_time == 0):
                    self._update_display(0)

        self.root.after(100, self.update_timer)

    # ---------- Счётчик повторений ----------
    def increment_counter(self, event=None):
        self.rep_counter += 1
        self.counter_label.config(text=str(self.rep_counter))

    def reset_counter(self):
        self.rep_counter = 0
        self.counter_label.config(text="0")

if __name__ == "__main__":
    root = tk.Tk()
    app = CrossfitTimer(root)
    root.mainloop()