#!/bin/bash
cd ./backend
git clone https://github.com/open-webui/open-webui.git temp-openwebui
cp -r temp-openwebui/backend/open_webui/* backend/open_webui/
cp temp-openwebui/backend/requirements.txt . # TODO mettre à jour le fichier requirements.txt avec uniquepent les dépendances du backend openwebui
rm -rf temp-openwebui
pip install -r requirements.txt
git add backend/open_webui requirements.txt
git commit -m "Updating Open WebUI backend"
git push
