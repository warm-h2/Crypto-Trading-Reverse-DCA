# Serhan's Reveres DCA Strategy

This project contains the implementation and execution (on Binance) of the reverse DCA strategy, the details of which are provided by Serhan.

## How to Run (via miniconda/anaconda)
* Clone the repository apollo_alpha_v2 strategy if not already cloned.
* It is preferrable to use miniconda and create a new python 3.9 environment in it with the name of rdca
* Install miniconda in the system.
* Open the miniconda terminal and create a new Python 3.9 environment in it with the name of rdca using the following command:
    * conda create –name rdca python=3.9
* Activate the newly created environment using the following command:
    * conda activate rdca
* Install the required Python packages mentioned in requirements.txt in the root directory using the following command:
    * pip install -r requirements.txt
* Set the following environment variable:
    * CONDAPATH: Path of the conda directory, e.g. D:/miniconda
* Set the required settings in the settings.ini file in the root directory
* Run _run.bat_ to start the execution

## How to Run (via system-wide python)
* Clone the repository apollo_alpha_v2 strategy if not already cloned.
* Install the required Python packages mentioned in requirements.txt in the root directory using the following command:
    * pip install -r requirements.txt
* Set the following environment variable:
    * CONDAPATH: Path of the conda directory, e.g. D:/miniconda
* Set the required settings in the settings.ini file in the root directory
* open the python terminal at the root dir and star the execution via the following command:
    * python main.py

## Notes
* The logs will be sent to the Telegram channel while the execution is running.
* If the execution stops for any reason, close the running terminal and positions manually and restart the terminal.