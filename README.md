# README — Caja Chica Gomería

## Requisitos
- Windows 10/11
- Python 3.11 o superior
- Git (recomendado, para sincronizar con GitHub)

## Instalación en la computadora de la oficina (primera vez)

1. **Instalar Python**
   - Ir a https://www.python.org/downloads/
   - Descargar la versión para Windows
   - **Importante**: al instalar, tildar la casilla **"Add Python to PATH"** antes de darle a Install. Si te la salteás, después hay que reinstalar.

2. **Verificar que se instaló**
   Abrir una terminal (en VS Code: menú *Terminal* → *New Terminal*) y escribir:
   ```
   python --version
   ```
   Debería mostrar algo como `Python 3.12.x`.

3. **Conseguir el proyecto**
   - Si ya está en GitHub:
     ```
     git clone https://github.com/TU-USUARIO/caja-chica-gomeria.git
     ```
   - Si todavía no, simplemente trabajar en la carpeta donde tengas los archivos (`plan_caja_chica.md`, `CLAUDE.md`, etc.)

4. **Entrar a la carpeta del proyecto**
   ```
   cd caja-chica-gomeria
   ```

5. **Crear un entorno virtual**
   Esto crea un "ambiente" aislado para las librerías de este proyecto, sin mezclarlas con otros programas Python que tengas instalados.
   ```
   python -m venv venv
   ```

6. **Activarlo**
   ```
   venv\Scripts\activate
   ```
   Vas a ver que el principio de la línea de la terminal cambia a algo como `(venv) C:\...` — eso confirma que está activo.

7. **Instalar las dependencias del proyecto**
   (cuando tengamos el archivo `requirements.txt`, que se crea al armar la estructura del proyecto)
   ```
   pip install -r requirements.txt
   ```

8. **Correr el programa**
   ```
   python app.py
   ```

9. **Abrir el navegador** en: `http://localhost:5000`

> 💡 Para no escribir estos comandos cada vez, cuando armemos el código vamos a crear un archivo `arrancar.bat` que hace todo esto con un doble clic, como una app de escritorio normal.

## Instalar en la otra computadora (también Windows)

1. Repetir los pasos 1-2 de arriba (instalar Python, verificar).
2. Conseguir el proyecto:
   - Con GitHub: `git clone https://github.com/TU-USUARIO/caja-chica-gomeria.git`
   - O copiando la carpeta por pendrive/red — pero **nunca copiar la carpeta `venv`**, hay que crearla de nuevo en cada computadora (paso 3 de abajo).
3. Repetir los pasos 5-8 de arriba: crear el entorno virtual **en esa compu**, activarlo, instalar dependencias, correr.

### ¿Y los datos que ya cargaste?
- Si querés que las dos computadoras vean los mismos movimientos de caja, vas a tener que copiar el archivo de la base de datos (algo como `caja.db`) de una a la otra a mano — eso no se sincroniza solo entre las dos compus.
- Si van a ser usos independientes, cada una puede tener su propia base sin problema.
- Esto lo afinamos cuando lleguemos a esa parte del armado.

## Nota de privacidad
El repositorio en GitHub va a ser **público** por ahora (se puede pasar a privado más adelante cuando se agreguen módulos con más datos de empleados). Por eso, el archivo real de base de datos (`caja.db` o similar), con los movimientos y montos reales de la empresa, **no se sube a GitHub** — queda excluido en `.gitignore`, sin excepción. Si necesitás llevar los datos de una compu a la otra, copiá ese archivo directamente (pendrive, etc.), no por GitHub.

Cualquier dato de ejemplo que aparezca en el código (para probar algo) debe ser ficticio — sin nombres reales de empleados ni montos reales de la empresa, ya que cualquiera puede ver el repositorio.
