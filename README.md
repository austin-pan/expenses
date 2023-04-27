# Expenses

Download CalTrain order history screenshots and upload them to SAP Concur
under a new expense report!

## Requirements

- Selenium Server Standalone
  ```shell
  brew install selenium-server
  ```
  - Java (1.8+)
    ```shell
    brew install openjdk@11
    # Will need to symlink Java if installing Java for the first 
    # time (as specified in brew install's caveats): 
    sudo ln -sfn /opt/homebrew/opt/openjdk@11/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk-11.jdk
    ```
- Selenium
  ```shell
  python3 -m pip install selenium
  ```
- Mozilla Firefox
  ```shell 
  brew install --cask firefox
  ```
  - Geckodriver
    ```shell
    brew install geckodriver
    ```

## Tutorial

This repository consists of two scripts. The first script
takes screenshots of CalTrain transaction receipts and the second script uploads
those receipts to SAP Concur. 

The scripts are not 100% automated: you will have to log into each service 
manually through the opened web browser and the second script does not automatically
submit the expense report in case you want to manually add more expenses or verify 
the report.

### CalTrain Tickets

Takes a screenshot of each CalTrain ticket up to the specified cutoff date. The
screenshots are saved to the specified output directory in the format of 
`{orderNumber}_{date}_{price}.png`.

When run, a browser window that is controlled by Selenium will open and navigate to
the CalTrain login page and wait. Once you've logged in, the script will navigate 
to the order history page and take a screenshot of each transaction until the
specified date (or to the end if no date is specified). After all screenshots 
have been taken, the browser will close itself.

```
$ python3 tickets.py -h
usage: tickets.py [-h] [-d DATE] output

Take screenshots of CalTrain orders.

positional arguments:
  output                the directory to save screenshots to

options:
  -h, --help            show this help message and exit
  -d DATE, --date DATE  optional. The date (MM/DD/YYYY) to stop crawling at, exclusive
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
expense report and then add an expense for each image in the specified input directory.
The script files each expense as a *parking* expense, fills in date and price
information, and uploads the corresponding image as the receipt. After uploading
all expenses, the script will hang until ENTER is pressed in the terminal.

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
