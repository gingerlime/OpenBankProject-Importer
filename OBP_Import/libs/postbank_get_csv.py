#!/usr/bin/env python
__author__ = [' Jan Alexander Slabiak (alex@tesobe.com)']
__license__ = """
  Copyright 211 Music Pictures Ltd / TESOBE

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

__doc__= """
Using Selenium RC2, install it with "pip install selenium"
need also =>selenium-2.0

This tool will take controll of a local firefox and downlaod the CSV File from PB.

TMP is in the obp_config, this is importen. No every System have a /tmp (Also related
to win32 systems) 

"""


import os
import sys

from obp_config import TMP
from libs.import_helper import show_here
from libs.debugger import debug
from selenium import webdriver

# The csv will download the to tmp/csv/
TMP_SUFFIX ='csv'
here = show_here()


def check_for_clean_tmp():
    """Check for an empty tmp/csv """
    # This function will check that the tmp/csv folder is
    # empty. Else we'll have problem woring with the file.

    # Sanity Check #1: 
    # Do we have tmp/ and tmp/csv
    # TODO: Move this to import_helper

    if os.path.exists(TMP) !=  True:
        os.makedirs(TMP)

    csv_save_path = os.path.join(os.getcwd(),TMP,TMP_SUFFIX)

    if os.path.exists(csv_save_path) != True:
        os.makedirs(csv_save_path)

    # Check for an empty folder. 
    if len(os.listdir(csv_save_path)) != 0:
        for item in os.listdir(csv_save_path):
            os.remove(os.path.join(csv_save_path,item))

    return csv_save_path


   



def get_csv_with_selenium(csv_save_path,Username,Password):
    """Getting CSV file via Firefox, controled by Selenium webdriver"""
    # LINK: http://seleniumhq.org/docs/03_webdriver.html#getting-started-with-selenium-webdriver

    # Setting up a Profile for Firefox.
    # There a the Proxy disabled (to make sure) and the 
    # that he is just download files with asking.
    fp = webdriver.FirefoxProfile()
    fp.set_preference("network.proxy.type", 0)
    fp.set_preference("browser.download.folderList",2)
    fp.set_preference("browser.download.manager.showWhenStarting",False)
    fp.set_preference("browser.download.dir",csv_save_path)
    # Need to set CSV to saveToDisk, else it's unknown for FF and he will ask.
    fp.set_preference("browser.helperApps.neverAsk.saveToDisk","text/csv")

    browser = webdriver.Firefox(firefox_profile=fp) # Get local session of firefox
    browser.get("https://banking.postbank.de/rai/login") # Load page
    assert "Postbank Online-Banking" in browser.title

    # Here we will inserting Username and Password:
    # find the element that's name attribute is nutzername and kennwort
    inputElement_username = browser.find_element_by_name("nutzername")
    inputElement_password = browser.find_element_by_name("kennwort")


    # send Username and Password
    inputElement_username.send_keys(Username)
    inputElement_password.send_keys(Password)
    # submit the Username and Password to Postbank.
    inputElement_password.submit()


    # This open the Main Page for Accounts, check for the Name.
    # Call the Transaction Page
    browser.get("https://banking.postbank.de/rai/?wicket:bookmarkablePage=:de.postbank.ucp.application.rai.fs.umsatzauskunft.UmsatzauskunftPage")
    assert "Postbank Online-Banking" in browser.title 


    # Call the CSV Link.
    # Warning!
    # The Postbank uses a :page counter, when the URL doesn't have the right page counter it will return
    # a error message. 
    result = browser.get("https://banking.postbank.de/rai/?wicket:interface=:3:umsatzauskunftpanel:panel:form:umsatzanzeigeGiro:umsatzaktionen:umsatzanzeigeUndFilterungDownloadlinksPanel:csvHerunterladen::IResourceListener::")
    browser.close()


def main():
    path_to_save = check_for_clean_tmp()
    get_csv_with_selenium(path_to_save)
    


if __name__ == '__main__':
    main()
