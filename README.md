#### Why?
This is basically a reverse DCA strategy where DCA adds to a losing trade until the stop loss is reached. So regular DCA mostly wins smaller profits and lose a large bet which will eventually wipe out all the profits taken beforehand. Inversely we add to a winning trade until a take profit is reached so that smaller losses are a general flow of this strategy but when take profit is reached we cover the losses and take a larger profit. That's it. 

#### Logic:
All cryptocurrencies above the 4H and 1D 40-period HMA are filtered and a position is opened when the price of the smallest period (1H) crosses the HMA (40) upwards for long. In this sense, the HMA with the smallest period is a trigger, and the other 2 large HMAs are baseline filters. Positions are added by multiplying the previous position by 1.5x at every 2% gain and adds $20,30,45,67.5 respectively, reaching a balance of $162.5.

The position can end in 3 ways.

1) Closing with a profit when it reaches the 9% point.
2) If there is a 4% fall from the head-to-head point before profit realization, with stop loss.
3) If any of the 1H, 4H or 1D HMA values ​​are broken, the position is closed immediately and scanning is restarted until max_positions are filled.

Below is the setting file with explanations commented. 

### [settings]

#ticker = auto ; When the ticker is auto, the coinfinder mode is on. The normal mode is to run it by entering the name of a single coin. Like DOGEUSDT.
### ticker = auto

#Max_positions = 3 ; It is activated when the ticker is auto. It is the maximum number of coins we will keep open at the same time. When this number drops, the scan starts again.
### Max_positions = 3

#initial_direction = Sell; It indicates whether the bot will work long or short. It's short in this case.

### initial_direction = Sell

#base_order_size = 20 ; The amount of the position opening in USD. ($20 in this case)
### base_order_size = 20

#volume_scale = 1.5 ; The value of the multiplier by which we will multiply the previous amount in each position increase. For example. If you enter with 20 dollars, it will open positions as 20, 30, 45 ... etc.
### volume_scale = 1.5

#increment_pct = 2 ; The step percent value which we'll increase the position. In this example, a new position is added every 2% gain until the take profit is reached. 
### increment_pct = 2

#stop_loss_pct = 2 ; This stop loss value is valid after the position is opened for the first entry price only. If the position reverts without making any buy-ins then it closes the position when it reaches this value.
### stop_loss_pct = 2

#breakeven_threshold_pct = -4 ; This value activates after the first buy-in order is made. It's generally set as 0, its purpose is to prevent loss by exiting the position at the breakeven point with the slightest fall. If the loss reaches to -4%, it stop losses at -4% loss from the averege entry price, not first entry price. 
### breakeven_threshold_pct = -4

#take_profit_pct = 9 ; The take profit target percent. Valid from the first entered price.
### take_profit_pct = 9

#Moving Average type and periods. HMA1 position opening trigger, others baseline filter. 0 = disabled
### sma_period = 0
### hma1_period = 40
### hma2_period = 40
### hma3_period = 40

#Moving Average time frames. 0 = disabled
### sma_timeframe = 0
### hma1_timeframe = 1H
### hma2_timeframe = 4H
### hma3_timeframe = 1D

#Telegram and binance api key and secret points.
### [telegram]
api_token = xx
channel_chat_id_1 = yy
channel_chat_id_2 = zz
### [binance]
api_key = yy
api_secret = zz

## How to Run (via miniconda/anaconda)
* It is preferrable to use miniconda and create a new python 3.10 environment in it with the name of rdca
* Install miniconda in the system.
* Open the miniconda terminal and create a new Python 3.10 environment in it with the name of rdca using the following command:
    * conda create –name rdca python=3.10
* Activate the newly created environment using the following command:
    * conda activate rdca
* Install the required Python packages mentioned in requirements.txt in the root directory using the following command:
    * pip install -r requirements.txt
* Set the following environment variable:
    * CONDAPATH: Path of the conda directory, e.g. D:/miniconda
* Set the required settings in the settings.ini file in the root directory
* Run _run.bat_ to start the execution

## How to Run (via system-wide python)
* It's good to use python 3.10 environment for this bot.
* Download and install Python version 3.10.10 (Windows or Mac). (When installing Python, make sure to check the All checkbox in the first window of the installation).
* Also, to run your bot safely, download and install Visual Studio Code if you don't already have it installed.
* Please install Python VS code extention in VS code environment.
* Install the required Python packages mentioned in requirements.txt in the root directory using the following command:
    * pip install -r requirements.txt
* Set the required settings in the settings.ini file in the root directory
* open the python terminal at the root dir and star the execution via the following command:
    * python main.py
* Or Run _run.bat_ to start the execution

## How to Run on Ubuntu Server
* To install Python 3.10 on Ubuntu, follow these steps:
    * Open the Terminal and run the following command.
        
        Update Ubuntu Linux Before Installing Python 3.10
        ```shell
        sudo apt update && sudo apt upgrade
        ```

        Install Python 3.10 on Ubuntu via APT Command
        ```shell
        sudo apt install python3.10
        ```

        Verifying the Python 3.10 Installation on Ubuntu    
        ```shell
        python3.10 --version
        ```

        Installing Python Pip on Ubuntu via Python 3.10
        ```shell
        sudo apt install python3-pip
        ```

        Upgrade Pip to the Latest Version on Ubuntu via Python 3.10
        ```shell
        python3 -m pip install --upgrade pip
        ```
* To install VS Code on Ubuntu, follow these steps:

    * Open the Terminal and run the following command.

        Install VS code using Snap package
        ```shell
        sudo snap install --classic code
        ```
* Install the required Python packages mentioned in requirements.txt in the root directory using the following command:
    
    ```shell
    pip install -r requirements.txt
    ```
## Notes
* The logs will be sent to the Telegram channel while the execution is running.
* If the execution stops for any reason, close the running terminal and positions manually and restart the terminal.
