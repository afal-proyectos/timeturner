python -m pip freeze > requirements.txt #librerias

deactivate #desactivar entorno virtual
Remove-Item -Recurse -Force .venv #borra el entorno virtual

python -m venv .venv        #crea el entorno virtual
.venv\Scripts\activate      #activa el entorno virtual
pip install -r requirements.txt    #instala los requerimientos