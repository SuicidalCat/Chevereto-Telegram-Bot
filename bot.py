#!/usr/bin/python3.7
# coding:utf-8

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from functools import wraps
from threading import Thread
import os
import os.path
import sys
import glob
import telegram
import requests
import configparser
import json
import uuid
import mimetypes
import magic
import logging

#錯誤logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

#加載config
config = configparser.ConfigParser()
config.read('config.ini')

def main():
    updater = Updater(config['BOT']['ACCESS_TOKEN'])#填你bot的API Key
    dp = updater.dispatcher
    #handler functions
    def send_typing_action(function):
        @wraps(function)
        def command_function(*args, **kwargs):
            bot, update = args
            bot.send_chat_action(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
            function(bot, update, **kwargs)
        return command_function

    @send_typing_action
    def help(bot, update):
        bot.send_message(chat_id=update.message.chat_id, text='Send me some pictures or image file. Available format: .jpg, .png, .bmp, .gif, 20MB max file size.')

    def privacy(bot, update):
        bot.send_message(chat_id=update.message.chat_id, text="This bot is only designed to rely your media file, all of your presonal data will not storage on our server, for more usage info please check the image host's ToS/AUP site, thank you.")

    def uptime(bot, update):
        uptime_command = os.popen("uptime")
        uptime_output = uptime_command.read()
        bot.send_message(chat_id=update.message.chat_id, text=uptime_output)

    def storage_status(bot, update):
        storage_status_command = os.popen("df -lh")
        storage_status_output = storage_status_command.read()
        bot.send_message(chat_id=update.message.chat_id, text=storage_status_output)

    def cache_status(bot, update):
        cache_path = os.getcwd()
        cache_files_count = str(len([name for name in os.listdir(cache_path) if os.path.isfile(os.path.join(cache_path, name))]) - 1)
        cache_files_size = str(cache_files_size_count(cache_path))
        cache_status_message = 'Current cache status:\nCache files count: ' + cache_files_count + '\nCache files size: ' + cache_files_size
        bot.send_message(chat_id = update.message.chat_id, text = cache_status_message)

    def cache_files_size_count(cache_path):
        size = 0
        for dirpath, dirnames, filenames in os.walk(cache_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                size += os.path.getsize(fp)
        return size

    def cache_clean(bot, update):
        cache_path = os.getcwd()
        cache_files_list = glob.glob(os.path.join(cache_path, "*.jpg", "*.cache"))
        for cache in cache_files_list:
            os.remove(cache) 
        bot.send_message(chat_id=update.message.chat_id, text='All upload cache are cleared')

    def restart_action():
        updater.stop()
        os.execl(sys.executable, sys.executable, *sys.argv)

    def restart(bot, update):
        update.message.reply_text('Bot is restarting...')
        Thread(target=restart_action).start()

    @send_typing_action
    def unknow_msg(bot, update):
        bot.send_message(chat_id=update.message.chat_id, text='Please send me pictures or image file only!')

    @send_typing_action
    def image(bot, update):
        image_id = update.message.photo[-1].file_id
        image_name = '%s.jpg' % str(uuid.uuid4())
        image = bot.getFile(image_id)
        image.download(image_name)
        update.message.reply_text('Download complete, now uploading to image host...')
        return_data = image_upload(request_format(image_name))
        if return_data['status_code'] == 200:
            uploaded_info = 'Upload succeeded!\nHere are your links to this image:\nWeb viewer: ' + return_data['image']['url_viewer'] + '\nOrigin size: ' + return_data['image']['url']# + '\n Medium size:' + return_data['medium']['url']
            update.message.reply_text(uploaded_info)
        else:
            print(return_data)
            update.message.reply_text('Image Host error! Please try again later.')
            os.remove(image_name)

    @send_typing_action
    def image_file(bot, update):
        allowed_image_file_format = 'image/jpeg image/png image/bmp image/gif'
        image_file_id = update.message.document.file_id
        image_file_name = '%s.cache' % str(uuid.uuid4())
        image_file = bot.getFile(image_file_id)
        image_file.download(image_file_name)
        image_file_mime = magic.from_file(image_file_name, mime=True)
        if image_file_mime in allowed_image_file_format:
            update.message.reply_text('Download complete, now uploading to image host...')
            return_data = image_upload(request_format(image_file_name))
            if return_data['status_code'] == 200:
                uploaded_info = 'Upload succeeded!\nHere are your links to this image:\nWeb viewer: ' + return_data['image']['url_viewer'] + '\nOrigin size: ' + return_data['image']['url']# + '\n Medium size:' + return_data['medium']['url']
                update.message.reply_text(uploaded_info)
            else:
                print(return_data)
                update.message.reply_text('Image Host error! Please try again later.')
                os.remove(image_file_name)
        else:
            update.message.reply_text('Please send me .JPG .PNG .BMP .GIF format file only!')
            os.remove(image_file_name)

    def image_upload(images):
        image_host = config['HOST']['IMAGE_HOST']
        image_host_api_key = config['HOST']['IMAGE_HOST_API_KEY']
        image_host_return_format = config['HOST']['IMAGE_HOST_RETURN_FORMAT']
        request_url = 'https://' + image_host + '/api/1/upload/?key=' + image_host_api_key + '&format=' + image_host_return_format
        upload_response = requests.post(request_url, files = images)
        print(upload_response)
        return upload_response.json()
    #構造upload請求
    def request_format(image_name):
        image_upload_request = []
        image_type = magic.from_file(image_name, mime=True)
        image_upload_request.append(('source' , (image_name , open(image_name , 'rb') , image_type)))
        print(image_type)
        print(image_upload_request)
        return image_upload_request
    #handlers
    #/help指令處理
    dp.add_handler(CommandHandler("help", help))
    #/privacy指令處理
    dp.add_handler(CommandHandler("privacy", privacy))
    #/uptime指令處理
    dp.add_handler(CommandHandler("uptime", uptime))
    #/storage_status指令處理
    dp.add_handler(CommandHandler("storage_status", storage_status))
    #/cache_status指令處理
    dp.add_handler(CommandHandler("cache_status", cache_status))
    #/cache_clean指令處理
    dp.add_handler(CommandHandler("cache_clean", cache_clean))
    #/restart指令處理
    dp.add_handler(CommandHandler("restart", restart, filters=Filters.user(username=config['BOT']['ADMIN_USER'])))
    #處理用戶發送的圖片
    image_handler = MessageHandler(Filters.photo, image)
    dp.add_handler(image_handler)
    #處理用戶發送的圖片文件
    image_file_handler = MessageHandler(Filters.document, image_file)
    dp.add_handler(image_file_handler)
    #處理用戶私聊發送的未知訊息
    unknow_msg_handler = MessageHandler(Filters.private, unknow_msg)
    dp.add_handler(unknow_msg_handler)
    #啓動進程
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
