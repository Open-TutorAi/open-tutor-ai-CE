#!/bin/bash
cd ./backend
git clone https://github.com/pr-elhajji/open-tutor-ai-CE.git temp-opentutorai
cp -r temp-opentutorai/backend/open_tutorai/* backend/open_tutorai/
cp temp-opentutorai/backend/requirements.txt . # TODO mettre à jour le fichier requirements.txt avec uniquepent les dépendances du backend opentutorai
rm -rf temp-opentutorai
pip install -r requirements.txt
git add backend/open_tutorai requirements.txt
git commit -m "Updating Open TutorAI backend"
git push
