@echo off
REM Script d'installation des dépendances pour le projet FIFI
setlocal enabledelayedexpansion

REM Vérifie la présence de Python
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo [ERREUR] Python n'est pas disponible dans le PATH.
    echo Installez Python 3.10+ et relancez ce script.
    exit /b 1
)

REM Crée l'environnement virtuel s'il n'existe pas
IF NOT EXIST .venv (
    echo Creation de l'environnement virtuel .venv ...
    python -m venv .venv
    IF ERRORLEVEL 1 (
        echo [ERREUR] Impossible de creer l'environnement virtuel.
        exit /b 1
    )
) ELSE (
    echo Environnement virtuel .venv deja present.
)

REM Active l'environnement virtuel
call .venv\Scripts\activate
IF ERRORLEVEL 1 (
    echo [ERREUR] Impossible d'activer l'environnement virtuel.
    exit /b 1
)

REM Met a jour pip et installe les dependances du projet
python -m pip install --upgrade pip
IF ERRORLEVEL 1 (
    echo [ERREUR] Impossible de mettre pip a jour.
    exit /b 1
)

pip install -e .
IF ERRORLEVEL 1 (
    echo [ERREUR] L'installation des dependances a echoue.
    exit /b 1
)

echo.
echo [SUCCES] Le projet FIFI est pret a etre utilise.
exit /b 0
