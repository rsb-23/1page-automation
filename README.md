# 1page-automation

This repository contains small automation scripts for day-to-day tasks.  
Technology Used : Python and Selenium

## Content

1. leetcode_dcc.py - To retrieve old submission of LeetCode Daily Coding Challenge and resubmit.

1. To optimize privacy settings of your Social Media accounts.
   - [Facebook](secureFB.py)
   - [Instagram](secureIG.py)
   - [LinkedIn](secureLI.py)

## Setup

1. Clone/ Download this repo.
1. Download and install latest web-browser & its compatible webdriver (like Chrome.exe and ChromeDriver.exe) for execution.  
   :warning: Issue with Chrome & Chromedriver version 103, use v104 instead
1. Setup a python virtual environment and run  
   `pip install -r requirements.txt`
1. Update binary location (line-29) and driver-path (line-30) of securer.py
1. Add your accounts' username and passwords in `cred.yml` file.
1. Run the script.
