@echo off
chcp 65001 >nul
echo ========================================
echo   CFS 修改器 - 打包为 EXE
echo ========================================
echo.

:: 检查 pyinstaller
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装 PyInstaller...
    pip install pyinstaller
)

echo.
echo 正在打包...
pyinstaller --onefile --windowed --name "CFS修改器" --clean cfs_trainer.py

echo.
if exist "dist\CFS修改器.exe" (
    echo ========================================
    echo   打包成功！
    echo   文件位置: dist\CFS修改器.exe
    echo ========================================
    copy "dist\CFS修改器.exe" "..\CFS修改器.exe" >nul
    echo   已复制到游戏根目录: ..\CFS修改器.exe
) else (
    echo 打包失败，请检查错误信息
)

echo.
pause
