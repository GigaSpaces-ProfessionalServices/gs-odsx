sed -i '/export PYTHONPATH=$(dirname $(pwd))/d' ~/.bash_profile

#echo 'export PYTHONPATH=$(dirname $(pwd))' >> ~/.bashrc
project_home_dir=$(dirname $(pwd))
python_path="export PYTHONPATH="$project_home_dir
echo "$python_path" >> ~/.bash_profile
echo 'eval "$(register-python-argcomplete odsx.py)"' >> ~/.bash_profile
.  ~/.bash_profile