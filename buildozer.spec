[app]
title = Bot Deploy
package.name = botdeploy
package.domain = com.BotDeploy
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,ttf
version = 1.0
requirements = python3,kivy,requests,pyjnius
orientation = portrait
icon.filename = %(source.dir)s/icon_transparent_style4.png
presplash.filename = %(source.dir)s/icon_transparent_style4.png
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 31
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.build_tools = 33.0.1
android.platform = 31

[buildozer]
log_level = 2
warn_on_root = 1
