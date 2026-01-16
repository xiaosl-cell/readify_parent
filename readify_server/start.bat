@echo off
chcp 65001
echo ===================================
echo Readify Server Startup Script
echo ===================================

:: 设置Java环境变量（如果需要）
:: set JAVA_HOME=C:\Program Files\Java\jdk-17
:: set PATH=%JAVA_HOME%\bin;%PATH%

echo [1/3] Cleaning previous build...
:: 清理之前的构建
call mvn clean

echo [2/3] Building project...
:: 编译打包项目
call mvn package -DskipTests

echo [3/3] Starting Readify Server...
echo ===================================
:: 运行Spring Boot应用
java -Dfile.encoding=UTF-8 -jar target\readify-0.0.1-SNAPSHOT.jar

pause