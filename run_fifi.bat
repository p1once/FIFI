@echo off
REM Lance l'application FIFI apres configuration
setlocal

IF NOT EXIST .venv (
    echo [ERREUR] Aucun environnement virtuel detecte.
    echo Lancez d'abord setup_env.bat pour installer les dependances.
    exit /b 1
)

call .venv\Scripts\activate
IF ERRORLEVEL 1 (
    echo [ERREUR] Impossible d'activer l'environnement virtuel.
    exit /b 1
)

echo Lancement de l'application FIFI...
python -m fifi_app.main %*
