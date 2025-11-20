@echo off
echo ========================================
echo   OncoVision Backend - Servidor Django
echo ========================================
echo.

REM Verificar si existe el entorno virtual
if not exist venv (
    echo ERROR: No se encontro el entorno virtual.
    echo Por favor, ejecute setup_backend.bat primero.
    pause
    exit /b 1
)

REM Verificar si existe la base de datos
if not exist db.sqlite3 (
    echo ADVERTENCIA: No se encontro la base de datos.
    echo Desea ejecutar las migraciones ahora? (S/N)
    set /p migrate=
    if /i "%migrate%"=="S" (
        echo.
        echo Activando entorno virtual...
        call venv\Scripts\activate.bat
        echo.
        echo Ejecutando migraciones...
        python manage.py migrate
        echo.
        echo Desea crear un superusuario? (S/N)
        set /p createuser=
        if /i "%createuser%"=="S" (
            python manage.py createsuperuser
        )
        echo.
    )
)

echo Activando entorno virtual...
call venv\Scripts\activate.bat
echo.

echo Iniciando servidor Django en http://0.0.0.0:8080/
echo.
echo Presione Ctrl+C para detener el servidor
echo ========================================
echo.

python manage.py runserver 0.0.0.0:8080
