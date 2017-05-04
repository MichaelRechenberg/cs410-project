# cs410-project
Repo for collaboration on SP 17 CS410 Project (Michael, Lily, and Grace)
Lily rulez Mike droolz

To install the required packages on your machine, download the conda package manager and run the following:

  conda env create -f environment.yml

Once the packages have been installed activate the environment with
  
  source activate cs410-project


After doing the conda install, you'll need to download the .whl
  for the google module we use to gather the top k google results

Go to https://pypi.python.org/pypi/google and download
  google-1.9.3-py2.py3-none-any.whl

Then execute:
  pip install google-1.9.3-py2.py3-none-any.whl
