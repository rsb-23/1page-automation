# 1page-automation

[![pre-commit](https://github.com/rsb-23/1page-automation/actions/workflows/pre-commit.yml/badge.svg)](https://github.com/rsb-23/1page-automation/actions/workflows/pre-commit.yml)

This repository contains small automation scripts for day-to-day tasks.  
Technology Used : Python and Selenium

## Content

1. leetcode_dcc.py - To retrieve old submission of LeetCode Daily Coding Challenge and resubmit.

2. To optimize privacy settings of your Social Media accounts.
   - [Facebook](secureFB.py)
   - [Instagram](secureIG.py)
   - [LinkedIn](secureLI.py)

## Setup

1. Clone/ Download this repo.
2. Download and install latest web-browser & its compatible webdriver (like Chrome.exe and ChromeDriver.exe) for execution.  
   :warning: Issue with Chrome & Chromedriver version 103, use v104 instead
3. Setup a python virtual environment and run  
   `pip install -r requirements.txt`
4. Update binary location (line-29) and driver-path (line-30) of securer.py
5. Add your accounts' username and passwords in `cred.yml` file.
6. Run the script.
