import os
import tempfile
from pathlib import Path

import telebot
from telebot import types

import media

# token for @bailandobot, revoke via @BotFather if it ever leaks again
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
  raise SystemExit("BOT_TOKEN is not set. Get one from @BotFather and export it.")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message: types.Message):
  blackpool: str = '''Вітання! Гра почалася. У MyMix тебе чекають нові знайомства і завдання по саморозвитку.
           Натисни на кнопку «Продовжити»
           Якщо ти не бачиш кнопку, натисни на іконку з чотирма квадратиками справа в рядку введення.
           Якщо зовсім нічого не зрозуміло, напиши /help потрібна допомога, і тобі допоможе жива людина'''
  bot.reply_to(message, blackpool)

@bot.message_handler(content_types=['voice', 'video_note'])
def convert_to_mp3(message: types.Message):
  if not media.ffmpeg_available():
    bot.reply_to(message, 'ffmpeg не встановлено, не можу обробити це повідомлення')
    return

  attachment = message.voice or message.video_note
  file_info = bot.get_file(attachment.file_id)
  downloaded = bot.download_file(file_info.file_path)

  with tempfile.TemporaryDirectory() as workdir:
    source = Path(workdir) / Path(file_info.file_path).name
    source.write_bytes(downloaded)
    converted = Path(workdir) / 'voice.mp3'
    try:
      media.to_mp3(source, converted)
      duration: float = media.probe_duration(source)
    except media.MediaError:
      bot.reply_to(message, 'Не вдалося конвертувати це повідомлення')
      return
    caption = 'Ось твій запис у mp3, тривалість {:.1f} с'.format(duration)
    with converted.open('rb') as audio:
      bot.send_audio(message.chat.id, audio, caption=caption,
                     reply_to_message_id=message.message_id)

@bot.message_handler(content_types=['text'])
def send_text(message: types.Message):
    if message.text.lower() == 'привіт':
        bot.send_message(message.chat.id, 'Привіт, '+message.chat.username)
    elif message.text.lower() == 'прощавай':
        bot.send_message(message.chat.id, 'Прощавай, '+message.chat.username)
    else:
      bot.send_message(message.chat.id, 'Я лише тільки навчаюсь')

if __name__=='__main__':
  bot.polling()
