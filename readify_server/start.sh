#!/bin/bash

echo "==================================="
echo "Readify Server Startup Script"
echo "==================================="

# 设置Java环境变量（如果需要）
# export JAVA_HOME=/usr/lib/jvm/java-17-openjdk
# export PATH=$JAVA_HOME/bin:$PATH

echo "[1/3] Cleaning previous build..."
# 清理之前的构建
mvn clean

echo "[2/3] Building project..."
# 编译打包项目
mvn package -DskipTests

echo "[3/3] Starting Readify Server..."
echo "==================================="
# 运行Spring Boot应用
java -jar target/readify-0.0.1-SNAPSHOT.jar