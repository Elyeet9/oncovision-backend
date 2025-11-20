@echo off
echo ========================================
echo   OncoVision Backend - Setup
echo ========================================
echo.

REM Verificar si Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no esta instalado o no esta en PATH
    echo Por favor, instale Python 3.10 o superior desde https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/5] Verificando Python...
python --version
echo.

echo [2/5] Creando entorno virtual...
if exist venv (
    echo El entorno virtual ya existe. Desea recrearlo? (S/N)
    set /p recreate=
    if /i "%recreate%"=="S" (
        echo Eliminando entorno virtual existente...
        rmdir /s /q venv
        python -m venv venv
    ) else (
        echo Usando entorno virtual existente.
    )
) else (
    python -m venv venv
)
echo.

echo [3/5] Activando entorno virtual...
call venv\Scripts\activate.bat
echo.

echo [4/5] Actualizando pip...
python -m pip install --upgrade pip
echo.

echo [5/5] Instalando dependencias...
pip install -r requirements.txt
echo.

echo ========================================
echo   Setup completado exitosamente!
echo ========================================
echo.
echo Proximos pasos:
echo 1. Configurar archivo .env (si no existe)
echo 2. Ejecutar migraciones: python manage.py migrate
echo 3. Crear superusuario: python manage.py createsuperuser
echo 4. Ejecutar run_backend.bat para iniciar el servidor
echo.
pause
