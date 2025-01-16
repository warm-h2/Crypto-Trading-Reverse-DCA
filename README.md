# Serhan's Reveres DCA Strategy

This project contains the implementation and execution (on Binance) of the reverse DCA strategy, the details of which are provided by Serhan.

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

#### [settings]

#ticker = auto ; Ticker auto olduğu zaman coinfinder modu çalışır. Normal modu tek coinin adını girerek çalıştırmaktır. DOGEUSDT gibi. 

#### ticker = auto

#Max_positions = 3 ; Ticker auto olduğunda devreye girer. Aynı aynda kaç coini open olarak tutacağımız maksimum değeridir. Bu sayı aşağı düştüğünde tarama tekrar başlar.

#### Max_positions = 3

#initial_direction = Sell; botun long mu yoksa short mu çalışacağını belirtir. 

#### initial_direction = Sell

#base_order_size = 20 ; USD değerinden pozisyon açılış miktarı. 

#### base_order_size = 20

#volume_scale = 1.5 ; Her pozisyon arttırımında bir önceki miktarı kaç ile çarpacağımız çarpanın değeri. Örnek. 20 dolarla girersen 20, 30, 45 olarak pozisyonları açar… vb. 

#### volume_scale = 1.5

#increment_pct = 2 ; Arttırım yapacağımız yüzdesel değer. Bu örnekte her %2 yükselişte yukardaki volume_scale miktarı kadar parayı üstüne koyarak devam ediyoruz. 

#### increment_pct = 2

#stop_loss_pct = 2 ; Bu stop loss değeri pozisyon açıldıktan sonra geçerlidir. Eğer hiç alım yapamadan pozisyon geriye düşerse bu değere ulaştığında pozisyonu kapatır. 

#### stop_loss_pct = 2

#breakeven_threshold_pct = -4 ; Bu değer ise açılış sonrası ilk ekleme yaptıktan sonra devreye girer. Paranın "breakeven" noktasından ne kadar geriye düşerse pozisyonu kapatacağını gösterir. Bu değer genelde 0 olarak setleniyor amacı en ufak bir geriye düşüşte kafa kafaya noktasında pozisyondan çıkarak kaybı engellemektır. Yukardaki gibi değer -4 olunca kafa kafaya noktasından %-4'e kadar esnetip o noktada kapat demek oluyor. 

#### breakeven_threshold_pct = -4

#take_profit_pct = 9 ; Başlangıçtan %9 kazanç oluştuğunda pozisyonu karla kapat. 

#### take_profit_pct = 9

#Moving Average türü ve periodları. HMA1 pozisyon açılış tetiği, diğerleri baseline filtre. 0 = disabled

#### sma_period = 0
#### hma1_period = 40
#### hma2_period = 40
#### hma3_period = 40

#Moving Average zaman dilimleri. 0 = disabled

#### sma_timeframe = 0
#### hma1_timeframe = 1H
#### hma2_timeframe = 4H
#### hma3_timeframe = 1D


#Telegram ve binance api key ve secret noktaları. 

#### [telegram]
#### api_token = xx
#### channel_chat_id_1 = yy
#### channel_chat_id_2 = zz

#### [binance]
#### api_key = yy
#### api_secret = zz

Strateji örneği: Yukarıdaki örnekte paraların 4H ve 1D'lik 40 period HMA'nın üzerinde olanların hepsi filtrelenir ve en küçük olan period (1H) fiyatının HMA(40)'ı yukarı cross etmesiyle pozisyon açılır. Bu anlamda en küçük periodlu olan HMA bir trigger, diğer 2 büyük HMA ise baseline filtre olmuş olur. Açılımlar en yüksek hacimli paralar üzerinden max_positions parametresi dolana kadar devam ederler. Pozisyon her %2 kazançta bir önceki pozisyonu 1.5x ile çarparak satın alım yapar ve sırasıyla 20,30,45,67.5 dolarlık ekleme yaparak 162.5 dolarlık bir balance'a ulaşır. 

Pozisyon 3 şekilde sonuçlanabilir. 
1) %9 noktasına geldiğinde karla kapanması.
2) Kar realizasyonu gerçekleşmeden kafakafaya noktasından %4 geriye düşme yaşarsa stop loss ile.
3) 1H, 4H veya 1D'lik HMA değerlerinden herhangi birtanesi kırılım yaşarsa pozisyon anında kapatılır ve max_positions dolana kadar tarama tekrar başlatılır. 


