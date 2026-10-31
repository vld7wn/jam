@echo off
rem Uploads the djem project to the private GitHub repo vld7wn/jam, branch karakurt/game-update.
chcp 65001 >nul
set "GIT=C:\Program Files\Git\cmd\git.exe"
set "BRANCH=karakurt/game-update"
set "REMOTE=https://github.com/vld7wn/jam.git"
cd /d "%~dp0..\.."

if not exist "%GIT%" (echo Git не найден: %GIT% & goto :fail)

"%GIT%" config user.email >nul 2>&1
if errorlevel 1 (
  echo Не задано имя автора коммитов. Выполни один раз:
  echo   "%GIT%" config --global user.name "Твоё имя"
  echo   "%GIT%" config --global user.email "почта@example.com"
  goto :fail
)

if not exist ".git" ("%GIT%" init || goto :fail)
"%GIT%" checkout -B %BRANCH% || goto :fail
"%GIT%" add -A || goto :fail
"%GIT%" commit -m "Karakurt: Revenge — game, models, Blender sources" || echo Нет новых изменений для коммита.

"%GIT%" remote get-url origin >nul 2>&1
if errorlevel 1 ("%GIT%" remote add origin %REMOTE% || goto :fail) else ("%GIT%" remote set-url origin %REMOTE% || goto :fail)

rem Git Credential Manager opens a browser window for the GitHub login.
"%GIT%" push -u origin %BRANCH% || goto :fail
echo.
echo Готово: https://github.com/vld7wn/jam/tree/%BRANCH%
pause
exit /b 0

:fail
echo.
echo Загрузка не выполнена. Пришли текст выше в чат.
pause
exit /b 1
