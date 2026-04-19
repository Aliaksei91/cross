import tkinter as tk
from tkinter import messagebox
import time
import threading
import speech_recognition as sr
import re


class CrossfitTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("CrossFit Timer: Голосовой счётчик")
        self.root.geometry("550x600")
        self.root.resizable(False, False)

        # Переменные таймера
        self.running = False
        self.paused = False
        self.countdown_mode = False
        self.start_time = 0
        self.elapsed_time = 0
        self.target_time = 0

        # Счётчик повторений
        self.rep_counter = 0

        # Голосовое распознавание
        self.voice_enabled = False
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.listening_thread = None

        # === Элементы интерфейса ===

        # Отображение времени
        self.time_label = tk.Label(root, text="00:00:00", font=("Helvetica", 48), fg="blue")
        self.time_label.pack(pady=20)

        # Кнопки управления таймером
        frame_buttons = tk.Frame(root)
        frame_buttons.pack(pady=10)

        self.start_btn = tk.Button(frame_buttons, text="Старт (с 0)", command=self.start_from_zero, width=12)
        self.start_btn.grid(row=0, column=0, padx=5)

        self.start_countdown_btn = tk.Button(frame_buttons, text="Обратный отсчёт", command=self.set_countdown,
                                             width=15)
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
        self.time_entry.insert(0, "00:01:00")

        self.set_btn = tk.Button(frame_countdown, text="Установить", command=self.set_custom_time)
        self.set_btn.pack(side=tk.LEFT, padx=5)

        # Счётчик повторений
        frame_counter = tk.Frame(root)
        frame_counter.pack(pady=20)

        tk.Label(frame_counter, text="Счётчик повторений:", font=("Helvetica", 12)).pack()
        self.counter_label = tk.Label(frame_counter, text="0", font=("Helvetica", 42), fg="green")
        self.counter_label.pack()

        # Кнопки управления счётчиком
        frame_counter_buttons = tk.Frame(frame_counter)
        frame_counter_buttons.pack(pady=10)

        self.reset_counter_btn = tk.Button(frame_counter_buttons, text="Сбросить счётчик", command=self.reset_counter,
                                           width=15)
        self.reset_counter_btn.pack(side=tk.LEFT, padx=5)

        self.voice_btn = tk.Button(frame_counter_buttons, text="🎤 Вкл. голос", command=self.toggle_voice, width=15,
                                   bg="lightgray")
        self.voice_btn.pack(side=tk.LEFT, padx=5)

        # Статус голосового распознавания
        self.voice_status_label = tk.Label(root, text="Голосовое управление: ВЫКЛ", fg="gray", font=("Helvetica", 10))
        self.voice_status_label.pack(pady=5)

        # Лог последней распознанной команды
        self.command_log_label = tk.Label(root, text="", fg="blue", font=("Helvetica", 9))
        self.command_log_label.pack(pady=5)

        # Подсказки
        tips_frame = tk.Frame(root)
        tips_frame.pack(side=tk.BOTTOM, pady=10)
        tk.Label(tips_frame, text="Нажмите Enter для +1 повторение", fg="gray", font=("Helvetica", 9)).pack()
        tk.Label(tips_frame, text="Пробел — Пауза/Возобновить", fg="gray", font=("Helvetica", 9)).pack()
        tk.Label(tips_frame, text="Голос: скажите 'один', 'два' или '1', '2' и т.д.", fg="green",
                 font=("Helvetica", 9)).pack()
        tk.Label(tips_frame, text="Голос: 'сброс' или 'reset' — сбросить счётчик", fg="green",
                 font=("Helvetica", 9)).pack()

        # Привязка клавиш
        self.root.bind('<Return>', self.increment_counter)
        self.root.bind('<space>', self.toggle_pause_space)

        # Обновление таймера
        self.update_timer()

    # ---------- Логика таймера (без изменений) ----------
    def start_from_zero(self):
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
        try:
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
        self.elapsed_time = total_seconds
        self.running = True
        self.paused = False
        self.start_time = time.time()
        self._enable_pause_stop()
        self.start_btn.config(state=tk.DISABLED)
        self.start_countdown_btn.config(state=tk.DISABLED)

    def set_custom_time(self):
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
        if seconds < 0:
            seconds = 0
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        self.time_label.config(text=f"{h:02d}:{m:02d}:{s:02d}")

    def update_timer(self):
        if self.running and not self.paused:
            current = time.time()
            if self.countdown_mode:
                remaining = self.target_time - (current - self.start_time)
                if remaining <= 0:
                    self._update_display(0)
                    self.stop()
                    messagebox.showinfo("Таймер", "Время вышло!")
                else:
                    self._update_display(remaining)
            else:
                elapsed = current - self.start_time
                self._update_display(elapsed)
        elif self.running and self.paused:
            if self.countdown_mode:
                self._update_display(self.elapsed_time)
            else:
                self._update_display(self.elapsed_time)
        elif not self.running:
            if self.countdown_mode and not self.running and self.elapsed_time > 0:
                self._update_display(self.elapsed_time)
            else:
                if not self.countdown_mode or (self.countdown_mode and self.elapsed_time == 0):
                    self._update_display(0)

        self.root.after(100, self.update_timer)

    # ---------- Счётчик повторений (клавиатура) ----------
    def increment_counter(self, event=None):
        self.rep_counter += 1
        self.counter_label.config(text=str(self.rep_counter))

    def reset_counter(self):
        self.rep_counter = 0
        self.counter_label.config(text="0")
        self.update_command_log("Счётчик сброшен")

    # ---------- Голосовое управление ----------
    def toggle_voice(self):
        if not self.voice_enabled:
            # Включаем голосовое распознавание
            self.voice_enabled = True
            self.voice_btn.config(text="🎤 Выкл. голос", bg="lightgreen")
            self.voice_status_label.config(text="Голосовое управление: ВКЛ (слушаю...)", fg="green")
            self.start_voice_listening()
        else:
            # Выключаем
            self.voice_enabled = False
            self.voice_btn.config(text="🎤 Вкл. голос", bg="lightgray")
            self.voice_status_label.config(text="Голосовое управление: ВЫКЛ", fg="gray")
            self.update_command_log("Голосовое управление выключено")

    def start_voice_listening(self):
        """Запускает фоновый поток для прослушивания голоса"""
        if self.listening_thread is None or not self.listening_thread.is_alive():
            self.listening_thread = threading.Thread(target=self.listen_for_commands, daemon=True)
            self.listening_thread.start()

    def listen_for_commands(self):
        """Функция для непрерывного прослушивания в отдельном потоке"""
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)

        while self.voice_enabled:
            try:
                with self.microphone as source:
                    # Слушаем короткую фразу (до 2 секунд)
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=2)

                # Распознаём на русском и английском
                try:
                    text_ru = self.recognizer.recognize_google(audio, language="ru-RU").lower()
                    self.process_voice_command(text_ru)
                except:
                    try:
                        text_en = self.recognizer.recognize_google(audio, language="en-US").lower()
                        self.process_voice_command(text_en)
                    except:
                        pass  # Не распознано

            except sr.WaitTimeoutError:
                pass  # Просто продолжаем слушать
            except Exception as e:
                if self.voice_enabled:
                    self.root.after(0, lambda: self.update_command_log(f"Ошибка: {str(e)}"))
                time.sleep(0.5)

    def process_voice_command(self, text):
        """Обрабатывает распознанный текст"""
        print(f"Распознано: {text}")  # Для отладки

        # Извлекаем числа из текста
        numbers = re.findall(r'\d+', text)

        # Словарь для преобразования слов-чисел
        word_numbers = {
            'один': 1, 'одна': 1, 'одно': 1, 'раз': 1,
            'два': 2, 'две': 2,
            'три': 3,
            'четыре': 4,
            'пять': 5,
            'шесть': 6,
            'семь': 7,
            'восемь': 8,
            'девять': 9,
            'десять': 10,
            'одиннадцать': 11,
            'двенадцать': 12,
            'тринадцать': 13,
            'четырнадцать': 14,
            'пятнадцать': 15,
            'шестнадцать': 16,
            'семнадцать': 17,
            'восемнадцать': 18,
            'девятнадцать': 19,
            'двадцать': 20,
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
        }

        # Проверяем на команду сброса
        if any(cmd in text for cmd in ['сброс', 'reset', 'сбросить', 'обнули']):
            self.root.after(0, self.reset_counter)
            self.root.after(0, lambda: self.update_command_log(f"🎤 Сброс счётчика по голосу: '{text}'"))
            return

        # Ищем числа в тексте
        number = None

        # Сначала ищем цифры
        if numbers:
            number = int(numbers[0])
        else:
            # Ищем слова-числа
            words = text.split()
            for word in words:
                if word in word_numbers:
                    number = word_numbers[word]
                    break

        # Если нашли число, добавляем к счётчику
        if number and 1 <= number <= 50:  # Ограничим разумными пределами
            self.rep_counter += number
            self.root.after(0, lambda: self.counter_label.config(text=str(self.rep_counter)))
            self.root.after(0, lambda: self.update_command_log(f"🎤 +{number} по голосу: '{text}'"))
        elif number:
            self.root.after(0, lambda: self.update_command_log(f"🎤 Число {number} вне диапазона (1-50)"))
        else:
            self.root.after(0, lambda: self.update_command_log(f"🎤 Не распознано число: '{text}'"))

    def update_command_log(self, message):
        """Обновляет лог последней команды"""
        self.command_log_label.config(text=message)
        # Очищаем через 3 секунды
        self.root.after(3000, lambda: self.command_log_label.config(text="") if self.command_log_label.cget(
            "text") == message else None)


if __name__ == "__main__":
    root = tk.Tk()
    app = CrossfitTimer(root)
    root.mainloop()