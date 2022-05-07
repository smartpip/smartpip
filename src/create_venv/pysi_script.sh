# create venv and activate the venv
python3 -m venv pysi_venv
cd ./pysi_venv
source bin/activate

#create soft link | source taget
ln -s ~/.pysi_rep/requests/requests-2.26.0 /site-packages/requests-2.26.0
ln -s ~/.pysi_rep/requests/requests-2.26.0.dist-info /site-packages/requests-2.26.0.dist-info