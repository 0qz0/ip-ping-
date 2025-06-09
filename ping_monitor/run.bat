@echo off
echo 正在启动IP监控工具...
set PYTHON_PATH=C:\Users\zzz\AppData\Local\Programs\Python\Python310\python.exe
if exist "%PYTHON_PATH%" (
    "%PYTHON_PATH%" src/main.py
) else (
    echo Python未找到，请检查安装路径
    echo 当前路径: %PYTHON_PATH%
    pause
    exit /b 1
)
if errorlevel 1 (
    echo 程序运行出错，请检查Python是否正确安装
    pause
    exit /b 1
)
pause 