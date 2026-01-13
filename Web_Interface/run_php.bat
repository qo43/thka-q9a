@echo off

IF NOT "%~1"=="" (
    php -S %1
) ELSE (
    ECHO Usage: 
    ECHO    run_php [ADDRESS]:[PORT]
)