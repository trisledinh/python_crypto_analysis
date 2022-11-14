# python_crypto_analysis
--step 1:
sudo apt update

--step 2:
sudo apt -y upgrade
python3 -V

--step 3:
sudo apt install -y python3-pip

--step 4:
sudo apt install -y build-essential libssl-dev libffi-dev python3-dev
--step 5:
sudo apt install -y python3-venv
--step 6:
mkdir environments
--step 7:
cd environments
python3 -m venv my_env
source my_env/bin/activate


------------------------------------------------
INSTALL TA_LIB IN UBUNTU

wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
sudo ./configure
sudo make
sudo make install
pip install ta-lib


--------------------------------------------------
INSTALL MONGODB

1. Open your WSL terminal (ie. Ubuntu) and go to your home directory: cd ~
2. Update your Ubuntu packages: sudo apt update
3. Import the public key used by the MongoDB package management system: 
wget -qO - https://www.mongodb.org/static/pgp/server-5.0.asc | sudo apt-key add -
--Create a list file for MongoDB: 
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/5.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-5.0.list
4. Reload local package database: sudo apt-get update
5. Install MongoDB packages: sudo apt-get install -y mongodb-org
6. Confirm installation and get the version number: mongod --version
7. Make a directory to store data: mkdir -p ~/data/db
8. Run a Mongo instance: sudo mongod --dbpath ~/data/db
9. Check to see that your MongoDB instance is running with: ps -e | grep 'mongod'
10. To exit the MongoDB Shell, use the shortcut keys: Ctrl + C

#Setup Service MongoDB for WSL2
curl https://raw.githubusercontent.com/mongodb/mongo/master/debian/init.d | sudo tee /etc/init.d/mongodb >/dev/null

sudo chmod +x /etc/init.d/mongodb

sudo service mongodb status

sudo service mongodb start

sudo service mongodb stop

--Connection String
mongodb://localhost:27018

# Add Github

echo "# python_crypto_analysis" >> README.md  
git init  
git add README.md  
git commit -m "first commit"  
git branch -M main  
git remote add origin https://access_token@github.com/trisledinh/python_crypto_analysis.git   
https://github.com/trisledinh/python_crypto_analysis.git  


--------------------------------------------------------------
--- INSTALL Python package------------------------------------

pip install python-binance  
pip install investpy  
pip install tensorflow  
pip install numpy  
pip install pandas  
pip install matplotlib  
pip install seaborn  
pip install pymongo  

pip install --user gate-api  

----CRONTAB ------------------------------------------------------------------------------------------------------  
*/5 * * * * /usr/bin/python3 /home/trild/environments/my_env/crypto/run_sync_data.py >> /home/trild/cron.log 2>&1


