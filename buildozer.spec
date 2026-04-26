[app]

title = Controle de Diarias
package.name = diarias
package.domain = org.seunome
source.dir = .
source.include_exts = py
version = 1.0
requirements = python3,kivy,reportlab
orientation = portrait
fullscreen = 1

[android]
android.permissions = WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True

[buildozer]
log_level = 2
