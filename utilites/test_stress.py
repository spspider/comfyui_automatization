#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from utilites import add_russian_stress

# Тест функции проставления ударений
test_texts = [
    "Привет, как дела?",
    "Спасибо за помощь!",
    "Сегодня хорошая погода.",
    "Я изучаю русский язык.",
    "Мама готовит обед дома."
]

print("🔤 Тестирование функции проставления ударений:")
print("-" * 50)

for text in test_texts:
    stressed = add_russian_stress(text)
    print(f"Исходный: {text}")
    print(f"С ударениями: {stressed}")
    print()