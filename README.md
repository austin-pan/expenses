# Expenses

Download CalTrain order history screenshots and upload them to SAP Concur
under a new expense report!

## Requirements

- Python 3.10+
- Python Libraries
  - selenium
  - tqdm
- Selenium Server Standalone
  - Java (1.8+)
- Mozilla Firefox
  - Geckodriver

## Installation

Install Selenium Server Standalone

```shell
brew install selenium-server
```

Install Java (1.8+) for running the Selenium JAR

```shell
brew install openjdk@11
# Will need to symlink Java if installing Java for the first
# time (as specified in brew install's caveats):
sudo ln -sfn /opt/homebrew/opt/openjdk@11/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk-11.jdk
```

Install FireFox

```shell
brew install --cask firefox
```

Install GeckoDriver for automating FireFox

```shell
brew install geckodriver
```

Install Python 3.10+

```shell
brew install python@3.11
```

Create virtual environment to keep library installations clean

```shell
python3.11 -m venv ~/.venv/expenses
```

Activate and install required Python libraries into virtual environment

```shell
source ~/.venv/expenses
python3 -m pip install requirements.txt
```


## Tutorial

This repository consists of two scripts. The first script
takes screenshots of CalTrain transaction receipts and the second script uploads
those receipts to SAP Concur.

The scripts are not 100% automated: you will have to log into each service
manually through the opened web browser and the second script does not automatically
submit the expense report in case you want to manually add more expenses or verify
the report.

### Activate Virtual Environment

Make sure to activate the virtual environment with the required Python libraries
so that the scripts can access them when running!

```shell
source ~/.venv/expenses/bin/activate
```

### CalTrain Tickets

Takes a screenshot of each CalTrain ticket up to the specified cutoff date. The
screenshots are saved to the specified output directory in the format of
`{orderNumber}_{date}_{price}.png`.

When run, a browser window that is controlled by Selenium will open and navigate to
the CalTrain login page and wait. Once you've logged in, the script will navigate
to the order history page and take a screenshot of each transaction from present back
until the specified date (or to the beginning of time if no date is specified). After
all screenshots have been taken, the browser will close itself.

```
$ python3 tickets.py -h
usage: tickets.py [-h] [-d DATE] output

Take screenshots of CalTrain orders.

positional arguments:
  output                the directory to save screenshots to

options:
  -h, --help            show this help message and exit
  -d DATE, --date DATE  optional. The date (MM/DD/YYYY) to stop crawling at, exclusive
  -p PRICES, --prices PRICES
                        optional. Comma-separated list of parking permit prices to restrict
                        to, e.g. `5.50,2.75`
```

#### Examples

Download all CalTrain orders after March 4th, 2023 into `~/Downloads/caltrain`
```shell
$ python3 tickets.py -d 03/04/2023 ~/Downloads/caltrain
```

Download all CalTrain orders into `~/Downloads/caltrain`
```shell
$ python3 tickets.py ~/Downloads/caltrain
```

### SAP Concur

Uploads all images in the specified input directory into SAP Concur. The image names are
parsed by splitting on `_` (underscore) to retrieve date and price information which are
used to populate the relevant fields when adding expenses.

When run, a browser window that is controlled by Selenium will open and navigate to
the SAP Concur login page and wait. Once you've logged in, the script will start a new
expense report and wait for the report details to be manually populated. Once the
report has been created, the script will start adding expenses for each image in the
specified input directory. The script files each expense as a *parking* expense, fills
in date and price information, and uploads the corresponding transaction image as the
attached receipt. After uploading all expenses, the script will hang until the browser
window is closed.

```
$ python3 concur.py -h
usage: concur.py [-h] input

Create an SAP Concur expense report.

positional arguments:
  input       the directory with receipts to upload

options:
  -h, --help  show this help message and exit
```

#### Example

Create an expense report and add an expense for every receipt in `~/Downloads/caltrain`
```shell
python3 concur.py ~/Downloads/caltrain
```
