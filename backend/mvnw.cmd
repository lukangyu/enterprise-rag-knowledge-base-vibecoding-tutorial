@echo off
@REM ----------------------------------------------------------------------------
@REM GraphRAG Maven Wrapper - Downloads and executes Maven
@REM ----------------------------------------------------------------------------

setlocal

set WRAPPER_JAR="%~dp0.mvn\wrapper\maven-wrapper.jar"
set WRAPPER_PROPERTIES="%~dp0.mvn\wrapper\maven-wrapper.properties"
set MAVEN_VERSION=3.9.6
set MAVEN_URL=https://repo.maven.apache.org/maven2/org/apache/maven/apache-maven/%MAVEN_VERSION%/apache-maven-%MAVEN_VERSION%-bin.zip
set WRAPPER_URL=https://repo.maven.apache.org/maven2/org/apache/maven/wrapper/maven-wrapper/3.2.0/maven-wrapper-3.2.0.jar

set MAVEN_HOME=%~dp0.mvn\wrapper\dists\apache-maven-%MAVEN_VERSION%
set MAVEN_CMD=%MAVEN_HOME%\bin\mvn.cmd

if not exist "%MAVEN_CMD%" (
    echo Downloading Apache Maven %MAVEN_VERSION%...
    if not exist "%~dp0.mvn\wrapper\dists" mkdir "%~dp0.mvn\wrapper\dists"
    
    powershell -Command "Invoke-WebRequest -Uri '%MAVEN_URL%' -OutFile '%~dp0.mvn\wrapper\dists\maven.zip'"
    if errorlevel 1 (
        echo Failed to download Maven
        exit /b 1
    )
    
    echo Extracting Maven...
    powershell -Command "Expand-Archive -Path '%~dp0.mvn\wrapper\dists\maven.zip' -DestinationPath '%~dp0.mvn\wrapper\dists' -Force"
    del "%~dp0.mvn\wrapper\dists\maven.zip"
)

if exist "%MAVEN_CMD%" (
    "%MAVEN_CMD%" %*
) else (
    echo Maven not found. Please install Maven 3.8+ and add to PATH
    echo Download from: https://maven.apache.org/download.cgi
    exit /b 1
)

endlocal
