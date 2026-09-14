[app]
title = PyNDS
project_dir = .
input_file = src/app.py
exec_directory = dist
project_file =
icon = assets/app.ico

[python]
# pyside6-deploy подставит Python текущего виртуального окружения.
python_path =
packages = Nuitka==4.1.1

[qt]
qml_files =
excluded_qml_plugins =
modules = Core,Gui,WebChannel,WebEngineCore,WebEngineWidgets,Widgets,Svg
plugins = styles,iconengines

[nuitka]
# Standalone удобнее для проверки наличия ресурсов Qt WebEngine.
mode = standalone
extra_args = --include-data-dir=src/ui=ui --include-data-files=src/spec_settings.json=spec_settings.json --windows-console-mode=disable
