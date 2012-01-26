#!/usr/bin/env python
# -*- coding: utf-8 -*
__author__ = ['simonredfern (simon@tesobe.com)',' Jan Alexander Slabiak (alex@tesobe.com)']
__license__ = """
  Copyright 2011/2012 Music Pictures Ltd / TESOBE

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


import os
import csv
import bson
import unittest
import obp_config
import obp_import_post_bank
import libs.to_utf8
import libs.transactions
import libs.postbank_get_csv


from bson import son
from pymongo import Connection 
from socket import gethostbyname
from libs.debugger import debug
from libs.import_helper import *

# This will start checking Database
# Drop, Create, Insert, Tables Style ,Drop
# Using on the testcase assertisNot instead of assertEqual,
# http://docs.python.org/library/unittest.html#deprecated-aliases


class TestMongoDBBasic(unittest.TestCase):

    def setUp(self):
        pass
        # TODO: It would be better to have a configuration file.
        # That would be loaded at this place. J.A.S

    def test_config_settings(self):
        self.assertEqual(obp_config.MONGODB_SERVER,'obp_mongod')
        self.assertEqual(obp_config.MONGODB_SERVER_PORT,27017)


    def test_host_entry(self):
        result = gethostbyname("obp_mongod") 
        #check for host entry 
        self.assertIsNot(result,None)

    def test_mongodb_connection(self):
        result = Connection('obp_mongod', 27017)
        self.assertIsNot(result,None)
        result.disconnect()

    def test_mongodb_database_collections(self):
        """
            Check  baisc function test for MongoDB. So we can ensure that all use function exist
            and are not gone. 
        """
        self.connection = Connection('obp_mongod', 27017)
        # This line below, ensure that we don't have dupiclaed db
        self.connection.drop_database('test_obp_import_db') 
        self.mongo_db = self.connection.test_obp_import_db
        result = self.mongo_db.collection_names()
        # Nothing for insert, so nothing is created, should return a 0 in len
        self.assertEqual(len(result), 0)
        
        should_result = [u'test_obp_import_db', u'system.indexes']
        self.mongo_db.test_obp_import_db.insert({'test':123})
        result = self.mongo_db.collection_names()
        self.assertEqual(result, should_result)
        self.connection.drop_database('test_obp_import_db')

        # Check for no collection in test_obp_import_db
        self.mongo_db = self.connection.test_obp_import_db
        result = self.mongo_db.collection_names()
        # Should return a 0 in len
        self.assertEqual(len(result), 0)


class TestSelenium(unittest.TestCase):
     
    def SetUp(self):
        return None
        

    def test_check_for_clean_tmp(self):
        # Check that we'll have the tmp/ and tmp/csv folder
        self.check_test = obp_config.TMP
        self.check_test_csv_folder = os.path.join(self.check_test,libs.postbank_get_csv.TMP_SUFFIX)

        libs.postbank_get_csv.check_for_clean_tmp()
        self.assertTrue(os.path.exists(self.check_test))
        self.assertTrue(os.path.exists(self.check_test_csv_folder))

        # Check for empty folder
        # This function is not done yet. It have to delete the files
        self.assertEqual(0,len(os.listdir(self.check_test_csv_folder)))


    def test_get_csv_with_selenium(self):
        # This will call the get_csv_with_selenium function and try to download
        # a csv file.

        # This will return the path where the file will be save too.
        # Make also sure it's empty
        self.path_for_save = libs.postbank_get_csv.check_for_clean_tmp()

        # Downloading the CSV file with Firefox. 
        libs.postbank_get_csv.get_csv_with_selenium(self.path_for_save)
    
        # This function belongs to the sanity checks. Is there a file?
        # We tesing this twice! 
        self.csv_file = preperar_csv_file(self.path_for_save)
        self.assertTrue(os.path.exists(os.path.join(self.path_for_save,self.csv_file)))


class TestImporting(unittest.TestCase):

      def setUp(self):
          self.connection = Connection('obp_mongod', 27017)
          self.mongo_db = self.connection.test_obp_import_db


      def test_string_insert(self):
          self.import_data ={u'Bank Account':u'1234561231'
                              ,u'Bank Info': [u'Tester',u'it']
                              ,u'Bank Number ':u'123'
                             } 
          result = self.mongo_db.test_obp_import_db.insert(self.import_data)
          test_db_collection = self.mongo_db.test_obp_import_db
          result = test_db_collection.find_one(result)
          self.assertEqual(result,self.import_data)
          #make differne insering of data, like fist a string, numerbs


      def test_number_insert_type(self):
          self.import_data ={u'Number insering':1234561231
                              ,u'Bank Number ':123
                             } 

          self.inserting_data = son.SON(self.import_data)
          result = self.mongo_db.test_obp_import_db.insert(self.inserting_data)
          test_db_collection = self.mongo_db.test_obp_import_db
          result = test_db_collection.find_one(result)
          for keys, values in result.items():
              if type(values) is bson.objectid.ObjectId:
                  continue
              elif type(values) is int:
                  self.values_eq_int = 1
              else:
                  self.values_eq_int = 0 
              self.assertEqual(self.values_eq_int,1)
              


class TestImportCSV(unittest.TestCase):
      """
          This Test will parse a CSV file. 
      """
      def setUp(self):
          self.connection = Connection('obp_mongod', 27017)
          self.mongo_db = self.connection.test_obp_import_db
          self.delimiter = ';'
          self.quote_char = '"'
    
          
          self.here = os.getcwd()
          self.csv_path = os.path.join(self.here, 'usr/tests')
          self.csv_file = 'test_example_latin1.csv'
          self.file = os.path.join(self.csv_path, self.csv_file)
          self.file_to_utf = os.path.join('usr/tests/',self.csv_file)


      def test_for_existing_csv(self):
          # Check first for the tests/test_example_latin1.csv file
          self.assertTrue(os.path.isfile(self.file))

      
      def test_CSV_converter_to_UTF8(self):
          #This call the to_utf8 function, and saves a file to tmp/
          result = libs.to_utf8.main(self.file)
          self.assertTrue(os.path.isfile(result))

          csv_reader = csv.reader(open(result, 'rb'),delimiter=';', quotechar='"')
          self.utf8_file = obp_import_post_bank.get_info_from_row(csv_reader.next())
          for element in self.utf8_file:
            if type(element) is unicode:
                self.values_eq_unicode = 1
            else:
                self.values_eq_unicode = 0
          self.assertEqual(self.values_eq_unicode,1)

          os.remove(result)
          self.assertFalse(os.path.isfile(result))

          result = os.getcwd()
          self.assertEqual(result,self.here)


      def test_Import_CSV(self):
          result = libs.to_utf8.main(self.file)
          self.assertTrue(os.path.isfile(result))

          csv_reader = csv.reader(open(result, 'rb'),delimiter=';', quotechar='"')
          self.utf8_file = obp_import_post_bank.get_info_from_row(csv_reader.next())
          for element in self.utf8_file:
            if type(element) is unicode:
                self.values_eq_unicode = 1
            else:
                self.values_eq_unicode = 0
          self.assertEqual(self.values_eq_unicode,1)


          self.connection = Connection('obp_mongod', 27017)
          self.mongo_db = self.connection.test_obp_import_db
          self.collection = self.mongo_db.test_obp_import_db.insert(son.SON(self.utf8_file))
          self.find_in_mongo = self.mongo_db.test_obp_import_db.find_one(self.collection)
          self.find_should = {
                  u'obp_transaction_date_complete': u'07.11.2011',
                  u'obp_transaction_new_balance': u'5.314',
                  u'obp_transaction_comment2': u'PETRA PFIFFIG',
                  u'obp_transaction_amount': u'-328',
                  u'obp_transaction_comment1': u'111111/1000000000/37050198 Finanzkasse 3991234 Steuernummer 00703434',
                  u'obp_transaction_data_blob': u'Finanzkasse K\xf6ln-S\xfcd',
                  u'obp_transaction_transaction_type_de': u'\xdcberweisung',
                  u'_id': "ObjectId('4eba776731533f464d000000')",
                  u'obp_transaction_date_start': u'07.11.2011'
                  }
          # This is a new test from Pyhon2.7, it will sort the input of the
          # test and then comapre them like assertEqual
          # LINK:
          # http://docs.python.org/library/unittest.html#unittest.TestCase.assertItemsEqual

          self.assertItemsEqual(self.find_should,self.find_in_mongo)

          os.remove(result)
          self.assertFalse(os.path.isfile(result))


      def test_CSV_imported_field_type(self):
          pass
          #result = type(self.find_in_mongo['obp_transaction_new_balance'])




    

#class TestTransationObject(unittest.TestCase)

             
         

if __name__ == '__main__':
    unittest.main()