@echo off
title Islam Fatwa Bot - Setup & Start
cls
if not exist .env (
    echo Keine Konfiguration gefunden. Starte Setup-Assistenten...
    python setup_wizard.py
) else (
    echo Starte den Islam Fatwa Bot...
    python main.py
)
pause
