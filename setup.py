#!/usr/bin/env python
"""
Script para inicializar el proyecto GATTO
Uso: python setup.py
"""
import os
import sys
import shutil
from pathlib import Path

def print_header(text):
    print(f"\n{'='*50}")
    print(f"  {text}")
    print(f"{'='*50}\n")

def check_env_file():
    """Verifica si existe el archivo .env"""
    print("🔍 Verificando archivo .env...")
    if os.path.exists(".env"):
        print("✅ Archivo .env ya existe")
        return True
    
    if os.path.exists(".env.example"):
        print("📋 Creando .env desde .env.example...")
        shutil.copy(".env.example", ".env")
        print("✅ Archivo .env creado")
        print("\n⚠️  Por favor, edita .env y agrega tu GEMINI_API_KEY")
        return True
    
    print("❌ No se encontró .env.example")
    return False

def check_dependencies():
    """Verifica que estén instaladas las dependencias"""
    print("📦 Verificando dependencias...")
    try:
        import flask
        import google.generativeai
        import dotenv
        print("✅ Todas las dependencias están instaladas")
        return True
    except ImportError as e:
        print(f"❌ Falta instalar: {e}")
        print("   Ejecuta: pip install -r requirements.txt")
        return False

def check_folders():
    """Verifica que existan todas las carpetas necesarias"""
    print("📁 Verificando estructura de carpetas...")
    folders = [
        "static",
        "static/css",
        "static/js",
        "static/img",
        "templates"
    ]
    
    all_exist = True
    for folder in folders:
        if os.path.exists(folder):
            print(f"  ✅ {folder}/")
        else:
            print(f"  ❌ Falta: {folder}/")
            all_exist = False
    
    return all_exist

def main():
    print_header("🐱 GATTO - Configuración Inicial")
    
    steps = [
        ("Verificando estructura", check_folders),
        ("Verificando dependencias", check_dependencies),
        ("Configurando variables de entorno", check_env_file),
    ]
    
    all_ok = True
    for step_name, step_func in steps:
        print(f"\n▶️  {step_name}...")
        if not step_func():
            all_ok = False
    
    print_header("Resumen")
    
    if all_ok:
        print("✅ ¡Setup completado correctamente!")
        print("\n📝 Próximos pasos:")
        print("  1. Edita el archivo .env con tu GEMINI_API_KEY")
        print("  2. Ejecuta: python app.py")
        print("  3. Abre: http://localhost:5000\n")
    else:
        print("❌ Hay algunos problemas que resolver:")
        print("  1. Instala las dependencias: pip install -r requirements.txt")
        print("  2. Crea un archivo .env con tu API key de Gemini")
        print("  3. Verifica que todas las carpetas existan\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
