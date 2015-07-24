###########################################################
#
# Copyright (c) 2005, Southpaw Technology
#                     All Rights Reserved
#
# PROPRIETARY INFORMATION.  This software is proprietary to
# Southpaw Technology, and is not to be reproduced, transmitted,
# or disclosed in any way without written permission.
#
#
#

__all__ = ["CsvExportCmd"]

import os, csv
import shutil
import re
from pyasm.search import SObjectFactory, SearchType, Search, SearchKey

from command import *


class CsvExportCmd(Command):


    def __init__(my, search_type, view, column_names, file_path):
        my.search_type = search_type
        my.view = view
        my.file_path = file_path
        my.search_ids = []
        my.search_keys = []
        my.column_names = column_names
        my.include_id = True

    def get_title(my):
        return "CSV Export"

    def check(my):
        return True

    def set_search_ids(my, search_ids):
        my.search_ids = search_ids

    def set_search_keys(my, search_keys):
        my.search_keys = search_keys

    def set_include_id(my, include):
        my.include_id = include

    def get_content(my):
        file = open(my.file_path)
        content = file.read()
        file.close()
        return content
 

    def execute(my):
        assert my.search_type
        assert my.view
        assert my.file_path

        search = Search(my.search_type)
        if my.search_ids:
            search.add_enum_order_by("id", my.search_ids)
            search.add_filters("id", my.search_ids)
            sobjects = search.get_sobjects()
        elif my.search_keys:

            sobjects = Search.get_by_search_keys(my.search_keys, keep_order=True)
            """
            search_codes = [SearchKey.extract_code(i) for i in my.search_keys if SearchKey.extract_code(i) ]
            if search_codes:
                search.add_filters("code", search_codes)
            else:
                search_ids = [SearchKey.extract_id(i) for i in my.search_keys if SearchKey.extract_id(i) ]
                search.add_filters("id", search_ids)
            """
        else:
            sobjects = search.get_sobjects()

        from pyasm.widget import WidgetConfigView
        from pyasm.web import Widget
        config = WidgetConfigView.get_by_search_type(my.search_type, my.view)
        
        columns = []
        if my.column_names:
            columns = my.column_names
        # should allow exporting ids only
        """
        else:
            if not config:
                columns = search.get_columns()
            else:
                columns = config.get_element_names()
        """
        if my.include_id:
            columns.insert(0, "id")

        # create the csv file
        org_file = file(my.file_path, 'w')
        csvwriter = csv.writer(org_file, quoting=csv.QUOTE_NONNUMERIC)

        # write the titles
        csvwriter.writerow(columns)

        elements = my.get_elements(config, columns)
        display_option_dict = {}
        # this is for widgets that do preprocessing on all sobjects
        for idx, element in enumerate(elements):
            element.set_sobjects(sobjects)
            element.preprocess()
            display_options = config.get_display_options(columns[idx])
            display_option_dict[element] = display_options
            
        for idx, sobject in enumerate(sobjects):
            values = []
            
            for element in elements:
                
                element.set_current_index(idx)
                value = element.get_text_value()
                if isinstance(value, Widget):
                    value = value.get_buffer_display()
                elif isinstance(value, basestring):
                    if isinstance(value, unicode):
                        value = value.encode('UTF-8', 'ignore')
                else:
                    value = str(value)

                options = display_option_dict.get(element)
                if options.get('csv_force_string')=='true' and value:
                    value= '#FORCESTRING#%s'%value
                values.append( value )
            # write the values as list
            csvwriter.writerow(values)

        org_file.close()


        file2 = open(my.file_path, 'r')
        mod_file_path = '%s_mod' %my.file_path
        mod_file = open(mod_file_path, 'w')
        for line in file2:
            mod_line = re.sub(r'(\'|\"|)(#FORCESTRING#)', '=\\1', line)
            mod_file.write(mod_line)

        # new file
        file2.close()
        mod_file.close()

        #os.unlink(my.file_path)
        shutil.move(mod_file_path, my.file_path)

    def get_elements(my, config, element_names):

        elements = []
        for idx, element_name in enumerate(element_names):

            # check to see if these are removed for this production
            #if element_name in invisible_elements:
            #    continue
            try:
                display_wdg = config.get_display_widget(element_name)

            except ImportError, e:
                print "WARNING: ", str(e)
                from tactic.ui.common import SimpleTableElementWdg
                display_wdg = SimpleTableElementWdg()
                display_wdg.set_name(element_name)

            elements.append(display_wdg)
            '''
            display_handler = config.get_display_handler(element_name)


            # else get it from default of this type
            if display_handler == "":
                display_handler = "SimpleTableElementWdg"
          
            from pyasm.widget import WidgetConfig
            element = WidgetConfig.create_widget( display_handler )
            element.set_name(element_name)
            elements.append(element)
            '''
        return elements









