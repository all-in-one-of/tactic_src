###########################################################
#
# Copyright (c) 2010, Southpaw Technology
#                     All Rights Reserved
#
# PROPRIETARY INFORMATION.  This software is proprietary to
# Southpaw Technology, and is not to be reproduced, transmitted,
# or disclosed in any way without written permission.
#
#
#

__all__ = ['DiscussionElementWdg', 'DiscussionWdg', 'DiscussionAddNoteWdg', 'DiscussionAddNoteCmd', 'DiscussionEditWdg', 'NoteStatusEditWdg']

from tactic.ui.common import BaseRefreshWdg, BaseTableElementWdg

from pyasm.common import Environment, TacticException, jsondumps, jsonloads, SPTDate, Common
from pyasm.biz import Pipeline, Project, File, IconCreator, Schema
from pyasm.command import Command, EmailTrigger2
from pyasm.web import DivWdg, Table, WikiUtil, HtmlElement, SpanWdg, Widget
from pyasm.search import Search, SearchType, SObject, SearchKey
from pyasm.widget import SwapDisplayWdg, CheckboxWdg, IconButtonWdg, IconWdg, TextWdg, TextAreaWdg, SelectWdg, ProdIconButtonWdg, HiddenWdg
from pyasm.prod.biz import ProdSetting
#from tactic.ui.panel import TableLayoutWdg
from tactic.ui.container import DialogWdg, MenuWdg, MenuItem
from pyasm.security import Login
from pyasm.widget import ThumbWdg

import dateutil, os

from tactic.ui.widget.button_new_wdg import ActionButtonWdg, IconButtonWdg

class DiscussionElementWdg(BaseTableElementWdg):
    #MTM made chronological, show_new_contexts
    ARGS_KEYS = {

    'process': {
         'description': 'Explicitly set the process for notes that can be added.',
         'category': 'Options',
         'order': 0
     },
    
    'context': {
        'description': 'Explicitly set the context(s) for notes that can be added.  This can be a list separated by commas',
        'category': 'Options',
        'order': 1
    },
    'use_parent': {
        'description': 'Determine whether or not to enter notes for parent sObject',
        'category': 'Options',
        'type': 'SelectWdg',
        'values': 'true|false',
        'order': 2
    }
    ,
    'show_fullscreen_button': {
        'description': 'Determine whether or not to show the expand notes icon button',
        'category': 'Options',
        'type': 'SelectWdg',
        'values': 'true|false',
        'order': 3
    },
    'note_format': {
        'description': 'Determine if the notes are shown in compact or full mode. Full- shows thumbnail, login-info, email and notes. Compact- shows just the notes.',
        'category': 'Options',
        'type': 'SelectWdg',
        'values': 'compact|full',
        'order': 4
    },

    'show_note_status': {
        'description': 'Determine whether or not to show the note status in abbreviated form.',
        'category': 'Options',
        'type': 'SelectWdg',
        'values': 'true|false',
        'order': 5
    },
    # FIXME: need a better name for this
    'show_context_notes': {
        'description': 'Determine if the notes in the context are hidden',
        'category': 'Options',
        'type': 'SelectWdg',
        'values': 'true|false',
        'order': 6
    },
     'chronological': {
        'description': 'True means the notes will all appear under one bar called "Notes" and will be in order of their timestamps',
        'category' : 'Options',
        'type' : 'SelectWdg',
        'values' : 'true|false',
        'order' : 7        
    },
     'show_new_contexts': {
        'description': 'True means the new notes will show what context they are and how many are new, above the actionable part of the widget',
        'category' : 'Options',
        'type' : 'SelectWdg',
        'values' : 'true|false',
        'order' : 8        
    },
    'note_expandable': {
        'description': 'Determine whether or not a note is expandable. True- shows a short version of the note that can be expanded. False- shows the full note',
        'category' : 'Options',
        'type' : 'SelectWdg',
        'values' : 'true|false',
        'order' : 9        
    },

    'append_process': {
        'description': 'Append a list of comma separated processes in addition of the ones defined in the pipeline',
        'category' : 'Options',
        'type' : 'TextWdg',
        'order' : 10        
    },

    'allow_email': {
        'description': 'Allow email to be sent out directly in this widget',
        'category' : 'Options',
        'type' : 'SelectWdg',
        'values' : 'true|false',
        'order': 11
    }

    }

  
   
    def is_editable(cls):
        return False
    is_editable = classmethod(is_editable)

    def handle_th(my, th, wdg_idx=None):

        edit_wdg = DiscussionEditWdg()
        my.menu = edit_wdg.get_menu()

        th.add(edit_wdg)


    def get_width(my):
        return 400
       
   

    def handle_layout_behaviors(my, layout):
        # in case the note widget appears more than once in a table
        if my.parent_wdg.drawn_widgets.get(my.__class__.__name__) == True:
            return

        version = my.parent_wdg.get_layout_version()
        if version == "2":
            pass
        else:
            layout.add_smart_styles("spt_discussion_element_top", {
                'margin': '-3px -4px -3px -6px',
                'min-width': '300px'
            } )

        # extra js_action on mouseover to assign the search key of the note to hidden input
        js_action ='''
           var sk_input = menu_top.getElement('.spt_note_action_sk');
           var note_top = bvr.src_el;
           sk_input.value = note_top.getAttribute('note_search_key');
            '''

        # disable the default activator
        # my.menu.set_activator_over(layout, 'spt_note_header', js_action=js_action)

        # add action triggle for context itself
        my.menu.set_activator_over(layout, 'spt_note', js_action=js_action)
        my.menu.set_activator_out(layout, 'spt_discussion_top')


        DiscussionWdg.add_layout_behaviors(layout, my.hidden, my.allow_email)
        


    def init(my):
       
        my.hidden = False
        my.allow_email = my.kwargs.get('allow_email') != 'false'
        my.discussion = DiscussionWdg(show_border='false', contexts_checked='false', add_behaviors=False,   **my.kwargs)
        

    def get_required_columns(my):
        '''method to get the require columns for this'''
        return []

    def preprocess(my):
        parent =  my.get_parent_wdg()
        if parent and parent.kwargs.get('__hidden__') in [True, 'True']:
            my.discussion.kwargs['hidden'] = True
            my.hidden = True
           
        my.discussion.set_sobjects(my.sobjects)

    def set_sobjects(my, sobjects, search=None):
        my.discussion.set_sobjects(sobjects)
        my.discussion.notes_dict = None
        super(DiscussionElementWdg, my).set_sobjects(sobjects)

      
    def get_display(my):
        # setting the index so that the proper key is used for note retrieval
        idx = my.get_current_index()
        my.discussion.set_current_index(idx)
        top = DivWdg()
        top.add_class("spt_discussion_element_top")

        sobject = my.get_current_sobject()

        # this is usually not necessary since we call set_sobjects() in preprocess already
        # but on Edit of a note thru FingerMenu, it is needed
        my.discussion.kwargs['search_key'] = sobject.get_search_key()

        top.force_default_context_menu()
        top.add(my.discussion)


        return top



    def get_header_option_wdg(my):
        #div = DivWdg()
        #button = ActionButtonWdg(title="Expand")
        #div.add(button)
        #return div
        return None


    def get_text_value(my):
        '''for csv export'''

        from dateutil import parser
        comment_area = []
        
        idx = my.get_current_index()
        my.discussion.set_current_index(idx)

        my.discussion.preprocess_notes()

        notes = my.discussion.get_notes()
        
        if not notes:
            return ''

        last_context = None
        for i, note in enumerate(notes):
            context = note.get_value('context')
            # explicit compare to None
            if last_context == None or context != last_context:
                comment_area.append( "[ %s ] " % context )
            last_context = context
            
            child_notes = note.get_child_notes()
            # draw note item
            date = note.get_value('timestamp')
            value = parser.parse(date)
            setting = "%Y-%m-%d %H:%M"
            date_value = value.strftime(setting)
            comment_area.append(note.get_value("login"))
            comment_area.append(date_value)
            comment_area.append(note.get_value("note"))
            comment_area.append('\n')
            if child_notes:
                for child_note in child_notes:
                    child_note_value = child_note.get_value('note')
                    comment_area.append( "Reply: %s" %child_note_value)
                    comment_area.append( '\n' )
        return ' '.join(comment_area)


class DiscussionEditWdg(BaseRefreshWdg):

    def init(my):
        my.top_class = 'spt_note_edit_panel'
        my.menu = MenuWdg(mode='horizontal', width = 40, height=16, top_class=my.top_class)
        #my.menu = MenuWdg(mode='horizontal', width = 25, height=20, top_class=my.top_class)

    def get_menu(my):
        return my.menu



    def get_display(my):
        ''' A container div housing the MenuWdg'''
        widget = DivWdg()
        widget.add_class(my.top_class)
        widget.add_styles('position: absolute; display: none')

        hidden = HiddenWdg('note_search_key')
        hidden.add_class('spt_note_action_sk')
        widget.add(hidden)


        
        widget.add(my.menu)

        #menu_item = MenuItem('action', label=IconWdg("Edit", IconWdg.EDIT))
        menu_item = MenuItem('action', label='edit')
        script = [] 
        script.append('''
            var sk = spt.get_cousin(bvr.src_el, '.spt_note_edit_panel','.spt_note_action_sk');
            if (sk) sk = sk.value;
           
            var server = TacticServerStub.get();
            var note = null;
            
            try {
                note = server.get_by_search_key(sk);
            }
            catch(e) {
                    spt.alert(spt.exception.handler(e));
                }
            
            var ok = function(value) {
                try{
                    var title = 'Saving Note';
                    server.update(sk, {note: value});
                    var menu = spt.table.get_edit_menu(bvr.src_el);
                    spt.discussion.refresh(menu.activator_el);

                }
                catch(e) {
                    spt.alert(spt.exception.handler(e));
                }
            }
            spt.prompt('Edit note [ ' + note.context + ' ]:', ok, 
            {title: 'Edit',
            text_input_default: note.note, 
            okText: 'Save'});

          

        ''')


        item_behavior = {
            'type': 'click_up',
            'cbjs_action': ';'.join(script)
        }
        menu_item.add_behavior(item_behavior)
        my.menu.add(menu_item)

        #menu_item = MenuItem('action', label=IconWdg("Delete", IconWdg.DELETE))
        menu_item = MenuItem('action', label='delete')
        script ='''
            
            var sk = spt.get_cousin(bvr.src_el, '.spt_note_edit_panel','.spt_note_action_sk');

            if (sk) sk = sk.value;
           
            var server = TacticServerStub.get();
            
            try {
                var note = server.get_by_search_key(sk);
                if (!note) {
                    spt.alert('This note ' + sk +  ' does not exist');
                    return;
                }
            }
            catch(e) {
                    spt.alert(spt.exception.handler(e));
                }
            var ok = function() {
                try{
                    var title = 'Deleting Note';
                        server.delete_sobject(sk);
                        var menu = spt.table.get_edit_menu(bvr.src_el);
                        spt.discussion.refresh(menu.activator_el);


                }
                catch(e) {
                    spt.alert(spt.exception.handler(e));
                }
            }

            var cancel = function() {};
            var note_sum = note.note;
            if (note.note.length > 50 ) 
                note_sum =  note.note.substring(0,50) + '...';
            
            spt.confirm('Delete this note?<br/><br/><div style="padding: 10px;border: 1px #aaa dotted">' + note_sum + '</div>' , ok, cancel);

        '''

        item_behavior = {
            'type': 'click',
            'cbjs_action': script
        }
        menu_item.add_behavior(item_behavior)
        my.menu.add(menu_item)
       
        menu_item = MenuItem('action', label='status')
        #menu_item = MenuItem('action', label=IconWdg("Status", IconWdg.FILM))
        script = [] 

     
        script.append('''
            var menu = spt.table.get_edit_menu(bvr.src_el);
            var sk = spt.get_cousin(bvr.src_el, '.spt_note_edit_panel','.spt_note_action_sk');
            if (sk) sk = sk.value;
           
            var server = TacticServerStub.get();
            var wdg = '';
            try {
                var class_name = 'tactic.ui.widget.NoteStatusEditWdg';
                var kwargs = {args: {search_key: sk}};
                var wdg = server.get_widget(class_name, kwargs);
            }
            catch(e) {
                    spt.alert(spt.exception.handler(e));
                }
            
            var ok = function(button) {
            
                var server = TacticServerStub.get();
                var status_sel  = button.getParent('.content').getElement("[name='note_status']");
                if (status_sel) {
                    var status = status_sel.value;
                    
                    try{
                        var title = 'Saving Note Status';
                        //server.start({title:title, description: title});

                        server.update(sk, {status: status});
                        //server.finish();
                        spt.discussion.refresh(menu.activator_el);
                    }
                    catch(e) {
                        spt.alert(spt.exception.handler(e));
                    }
                }
                    
            };
            
            spt.prompt('Edit note status:', ok, 
            {title: 'Edit Note Status',
             okText: 'Save',
            custom_html: wdg
            });
            '''
        )

        item_behavior = {
            'type': 'click_up',
            'cbjs_action': ';'.join(script)
        }
        menu_item.add_behavior(item_behavior)
        my.menu.add(menu_item)

        return widget

class DiscussionWdg(BaseRefreshWdg):
    '''Special widget to add work hours'''

    HELP = "discussion-wdg"

    def init(my):
        my.process = ''
        my.contexts = []
        my.use_parent = my.kwargs.get('use_parent') 
        my._load_js = False

        my.notes_dict = None
        
        # we need to collect all the parents of the notes for preprocess search
        my.parent_dict = {}
        my.parents = []
        my.parent_processes = []
        my.append_processes = my.kwargs.get('append_process')
        my.allow_email = my.kwargs.get('allow_email')
        #MTM down to ...
        my.override_processes = my.kwargs.get('override_processes')
        my.preppend = ''#MTM
        if 'preppend' in my.kwargs.keys():#MTM
            my.preppend = my.kwargs.get('preppend')#MTM
        my.search_key = ''
        my.st = ''
        my.try_tree = False
        my.try_field = ''
        my.chrono = False
        my.chrono_name = 'Notes'
        my.show_new_contexts = True
        my.orig_c_new = {}
        my.c_new = {}
        my.context_counts = {}
        my.context_codes = {}
        if 'chronological' in my.kwargs.keys():
            if my.kwargs.get('chronological') in [True,'true','True','t','1',1]:
                my.chrono = True
        if 'show_new_contexts' in my.kwargs.keys():
            if my.kwargs.get('show_new_contexts') in [False,'false','False','0',0]:
                my.show_new_contexts = False
        my.login = ''
        #login_obj = Environment.get_login()
        lsear = Search("sthpw/login")
        lsear.add_filter('login',Environment.get_user_name())
        login_obj2 = lsear.get_sobject()
        my.preferences = login_obj2.get_value('twog_preferences')
        my.highlight = True
        if 'highlight_notes=false' in my.preferences:
            my.highlight = False
        my.show_note_top = True
        if 'show_note_counts=false' in my.preferences:
            my.show_note_top = False
        #...MTM Here
        #Might want to delete some of the stuff above. Not all of it needs to be used





    def get_onload_js(my):
        return '''
        spt.discussion = {};
        spt.discussion.refresh = function(src_el) {
            var discussion_top = spt.has_class(src_el, 'spt_discussion_top') ? src_el: src_el.getParent(".spt_discussion_top");
            // find out which contexts are open
            var contexts = discussion_top.getElements(".my_context");
            var default_contexts_open = [];
            for (var i = 0; i < contexts.length; i++) {
                if (contexts[i].getAttribute("spt_state") == 'open') {
                    var context = contexts[i].getAttribute("my_context");
                    if (context.strip())
                        default_contexts_open.push(context);
                }
            }
            spt.panel.refresh(discussion_top, {default_contexts_open: default_contexts_open, is_refresh: 'true'});
        }'''



    def add_layout_behaviors(cls, layout, hidden=False, allow_email=True):
        '''hidden means it's a hidden row table'''
        
        layout.add_relay_behavior( {
            'type': 'mouseup',
            'bvr_match_class': 'spt_note_attachment',
            'cbjs_action': '''
            var code_str = bvr.src_el.getAttribute("spt_note_attachment_codes");
            var server = TacticServerStub.get();
            var codes = code_str.split("|");
            for (var i = 0; i < codes.length; i++) {
                // get the files for this snapshot
                var path = server.get_path_from_snapshot(codes[i], {mode:'web'});
                window.open(path);
            }
            '''
        } )


        preppend = ''
        match_class = cls.get_note_class(hidden, 'spt_discussion_add')
        layout.add_relay_behavior( {
            'type': 'mouseup',
            'bvr_match_class': match_class,
            'hidden': hidden,
            'allow_email': allow_email,
            'cbjs_action': '''

            var top = bvr.src_el.getParent(".spt_dialog_top");
            var preppend = "%s";
            if (top == null) {
                top = bvr.src_el.getParent(".spt_discussion_top");
            }

            var container = top.getElement(".spt_add_note_container");
            var add_note = container.getElement(".spt_discussion_add_note");

            if (! add_note) {
                var kwargs = container.getAttribute("spt_kwargs");
                kwargs = kwargs.replace(/'/g, '"');
                kwargs = JSON.parse(kwargs);
                if(preppend != '' && preppend != null){
                    kwargs['preppend'] = preppend;
                }
                var layout = spt.table.get_layout();
                var upload_id = layout.getAttribute('upload_id')
                kwargs.upload_id = upload_id; 
                kwargs.hidden = bvr.hidden;
                kwargs.allow_email = bvr.allow_email;
                var class_name = 'tactic.ui.widget.DiscussionAddNoteWdg';
                spt.panel.load(container, class_name, kwargs, {},  {fade: false, async: false});
                add_note = top.getElement(".spt_discussion_add_note");
                spt.toggle_show_hide(add_note);
            }

            //new Fx.Tween(add_note,{duration:"short"}).start('margin-top', 0);

            // select the appropriate context or process
            var select = add_note.getElement(".spt_add_note_process");
            if (select) {
                var process = bvr.src_el.getAttribute("spt_process");
                var context = bvr.src_el.getAttribute("spt_context");

                var match = process ? process : context;
                for(var i = 0; i < select.options.length; i++) {
                  
                    if (select.options[i].value == match) {
                        select.selectedIndex = i;
                        break;
                    }
                }
            }

            ''' % preppend
            } )


        # DEPRECATED?
        # for expand note widget
        layout.add_relay_behavior( {
            'type': 'mouseup',
            'bvr_match_class': 'spt_discussion_expand',
            'cbjs_action': '''
            var top = bvr.src_el.getParent(".spt_discussion_top");
            var float = top.getElement(".spt_float");
            var clone = spt.behavior.clone(top);

            expand = clone.getElement(".spt_discussion_expand");
            spt.hide(expand);

            var code = bvr.src_el.getAttribute('code')
            var title = "Notes: " + code;
            var element_name = bvr.src_el.getAttribute('search_key')

            spt.tab.set_main_body_tab();
            spt.tab.add_new(element_name, title);
            spt.tab.load_node(element_name, clone);
            spt.tab.select(element_name);


            var notes = clone.getElements(".spt_note_content");
            for ( var i = 0; i < notes.length; i++ ) {
                spt.show( notes[i] );
            }

            '''
            } )

        submit_class = cls.get_note_class(hidden, 'spt_discussion_submit') 
        # for the Submit button
        layout.add_relay_behavior( {
        'type': 'mouseup',
        'bvr_match_class': submit_class,
        'cbjs_action': '''
        var preppend = "%s";
        var note_top = bvr.src_el.getParent(".spt_add_note_top");
        var values = spt.api.get_input_values(note_top, null, false);
        if (values.note == '') {
            spt.alert("Please enter a note before saving");
        }
        else {
            spt.app_busy.show("Adding note ...");

            var top = bvr.src_el.getParent(".spt_discussion_add_note");
            var attach_top = top.getElement(".spt_attachment_top");
            var ticket_key = attach_top.getAttribute('ticket_key');
            var files = attach_top.files;
            var server = TacticServerStub.get();
            if (!ticket_key)
                server.start({title: 'New Note', transaction_ticket: ticket_key});

            if (typeof(files) != 'undefined') {
                /*
                for (var i = 0; i < files.length; i++) {
                    spt.app_busy.show("Uploading ...", files[i]);
                    server.upload_file(files[i], ticket_key);
                }
                */
                spt.app_busy.hide()

                values['files'] = files;
                values['ticket'] = ticket_key;
            }
            else {
                values['files'] = [];
            }
            // rename add_process and add_context for the Cmd
            var process = values.add_process;
            values['process'] = process;
            var context = values.add_context;
            values['context'] = context;
            values['preppend'] = preppend;
            delete values.add_process;
            delete values.add_context;

            var cmd = 'tactic.ui.widget.DiscussionAddNoteCmd';
            
            try{
                server.execute_cmd(cmd, values);
                server.finish();
            }
            catch (e) {
                spt.alert(spt.exception.handler(e));
                server.abort();
            }

            spt.discussion.refresh(top);

            spt.app_busy.hide();
        }
        ''' % preppend
        })
 

    add_layout_behaviors = classmethod(add_layout_behaviors)




    def _get_parent(my, sobject):
        '''caching is automatically done in SObject level''' 
        parent = sobject.get_parent()
        return parent

    def get_note_class(cls, hidden, cls_name):
        ''' An attempt to separate the main table relay and hidden table relay. Otherwise it will toggle twice making it look like the button doesn't work'''
        if hidden == True:
            return '%s_hidden'%cls_name
        else:
            return cls_name

    get_note_class = classmethod(get_note_class)

    def preprocess_notes(my):
        '''this call get_all_notes once by design to build the dict''' 
        # this check stops this method from being called more than once per table
        insert_mode = False
        if len(my.sobjects) == 1 and my.sobjects[0].is_insert():
            insert_mode = True
            my.notes_dict = {}

        if my.notes_dict != None or insert_mode:
            return my.notes_dict 
        # collect my.parents 
        # use_parent and sobject option are mutually exclusive for now 
        # I think this is only used for a single object view with notes
        my.parent = my.kwargs.get("sobject")
        if not my.parent:
            if my.sobjects:
                has_process = my.sobjects[0].has_value('process')
                if my.use_parent == 'true':

                    for sobject in my.sobjects:
                        process = ''
                        if has_process:
                            process = sobject.get_value('process')
                        # this is used in the key for note_dict
                        my.parent_processes.append(process)
                        parent = my._get_parent(sobject)
                        # must append even if it is None
                        my.parents.append(parent)
                else:
                    my.parents = my.sobjects
            else: # indiviual update     
                search_key = my.kwargs.get("search_key")
                assert search_key
                my.parent = Search.get_by_search_key(search_key)
                # this is required for refresh
                has_process = my.parent.has_value('process')
                my.sobjects = [my.parent]
                if my.use_parent == 'true':
                    process = ''
                    if has_process:
                        process = my.parent.get_value('process')
                    # this is used in the key for note_dict
                    my.parent_processes.append(process)
                    
                    parent = my.parent.get_parent()
                    # must append even if it is None
                    my.parents.append(parent)
                else:
                    my.parents = [my.parent]
        else:
            my.parents = [my.parent]


        # append processes can't be used in conjuntion with use_parent when it has_process
        # in this case since this is meant for task or snapshot notes
        if has_process and my.use_parent =='true':
           my.append_processes = ''

       

        if my.use_parent == 'true':
            pass
          
        else:
            my.process = my.kwargs.get("process")
            # TODO: this needs to be eval to be a list if it's a comma separated string
            my.contexts = my.kwargs.get("context")
            if my.contexts and isinstance(my.contexts, basestring):
                my.contexts = my.contexts.split(',')
                my.contexts =[x.strip() for x in my.contexts if x.strip()]


        
        my.get_all_notes()


    def get_all_notes(my):
        ''' this is called by get_notes() in the very first get_display() since we dont have preprocess for BaseRefreshWdg'''
        my.search_key = my.kwargs.get("search_key") #MTM to end of function
        sob_code_s = my.search_key.split('code=')
        sob_code = ''
        if len(sob_code_s) > 1:
            sob_code = sob_code_s[1]
        my.st = my.search_key.split('?')[0]
        my.try_tree = False
        my.try_field = ''
        st_lookup = {'twog/order': 'order_code', 'twog/title': 'title_code', 'twog/proj': 'proj_code', 'twog/work_order': 'work_order_code'}  
        if 'treedown' in my.kwargs.keys():
            if my.st in st_lookup.keys():
                my.try_tree = True
                my.try_field = st_lookup[my.st]
       

        my.notes_dict = {}

        # maintain index but we want to filter out deleted parents (None)
        notes = []
        if not my.try_tree:
            my.filtered_parents = [p for p in my.parents if p]
            search = Search("sthpw/note") 
            search.add_relationship_filters(my.filtered_parents)
            if not my.chrono:
                search.add_order_by("process") # MTM KILL
                search.add_order_by("context") # MTM KILL   
            search.add_order_by("timestamp desc")
    
            if my.process:
                search.add_filter("process", my.process)
    
            if my.contexts:
                search.add_filters("context", my.contexts)
    
            notes = search.get_sobjects()
            has_process = my.sobjects[0].has_value('process')
            for note in notes:
                search_type = note.get_value("search_type")
                search_id = note.get_value("search_id")
                if my.use_parent == 'true' and has_process:
                    process = note.get_value("process")
                    key = "%s|%s|%s" % (search_type, search_id, process)
                else:
                    key = "%s|%s" % (search_type, search_id)
                notes_list = my.notes_dict.get(key)
                if notes_list == None:
                    notes_list = []
                    my.notes_dict[key] = notes_list
                notes_list.append(note)
        else:
            #my.filtered_parents = [p for p in my.parents if p]
            search = Search("sthpw/note") 
            parent_codes = []
            for p in my.parents:
                parent_codes.append(p.get_value('code'))
            search.add_filters(my.try_field, parent_codes)
            if not my.chrono:
                search.add_order_by("process") # MTM KILL
                search.add_order_by("context") # MTM KILL
            search.add_order_by("timestamp desc")
    
            if my.process:
                search.add_filter("process", my.process)
    
            if my.contexts:
                search.add_filters("context", my.contexts)
    
            notes = search.get_sobjects()
            has_process = my.sobjects[0].has_value('process')
            for note in notes:
                search_type = note.get_value("search_type")
                search_id = note.get_value("search_id")
                if my.use_parent == 'true' and has_process:
                    process = note.get_value("process")
                    key = "%s|%s|%s" % (search_type, search_id, process)
                else:
                    key = "%s|%s" % (search_type, search_id)
                find_field = note.get_value(my.try_field)
                if find_field not in my.notes_dict.keys():
                    my.notes_dict[find_field] = []
                my.notes_dict[find_field].append(note)  
        from pyasm.biz import Snapshot
        snapshots = Snapshot.get_by_sobjects(notes,context="publish") #MTM SPECIFIED THE CONTEXT
        my.attachments = {}
        for snapshot in snapshots:
            parent_key = snapshot.get_parent_search_key()
            xx = my.attachments.get(parent_key)
            if not xx:
                xx = []
                my.attachments[parent_key] = xx
            xx.append(snapshot)


        return my.notes_dict
  
    
    def make_timestamp(my):
        #MTM
        import datetime
        now = datetime.datetime.now()
        return now.strftime("%Y-%m-%d %H:%M:%S") 

    def get_time_date_dict(my, str_time):
        #MTM
        import datetime
        pre_split = str_time.split('.')[0]
        first_split = pre_split.split(' ')
        date = first_split[0]
        time = first_split[1]
        date_split = date.split('-')
        dt = {}
        dt['year'] = int(date_split[0])
        dt['month'] = int(date_split[1])
        dt['day'] = int(date_split[2])
        dt['date'] = date
        dt['time'] = time
        time_split = time.split(':')
        dt['hour'] = int(time_split[0])
        dt['minute'] = int(time_split[1])
        dt['second'] = int(time_split[2])
        dt['big_time'] = float((dt['hour'] * 3600) + (dt['minute'] * 60) + dt['second'])
        dt['str'] = str_time
        dt['dt'] = datetime.datetime(dt['year'], dt['month'], dt['day'], dt['hour'], dt['minute'], dt['second'])
        return dt
    
    def get_notes(my):
        my.preprocess_notes()
        # this is -1 for a single sobject refresh like after an edit, which works like 0
        idx = my.get_current_index()

        # getting sobj here instead of using my.parent since my.parent could change with the use_parent option
        my.sobject = my.sobjects[idx]
        my.parent = None
        if my.sobject.is_insert():
            return []


        my.parent = my.parents[idx]
        has_process = my.sobject.has_value('process')

        if not my.parent:
            key = ""
#        else:
#            search_type = my.parent.get_search_type()
#
#            from pyasm.biz import Schema
#            schema = Schema.get()
#            attrs = schema.get_relationship_attrs("sthpw/note", search_type)
#            attrs = schema.resolve_relationship_attrs(attrs, "sthpw/note", search_type)
#            from_col = attrs.get("from_col")
#            to_col = attrs.get("to_col")
#            search_code = my.parent.get_value(to_col)
#
#            #database_type = my.parent.get_database_type()
#            #if database_type == "MongoDb":
#            #    search_code = my.parent.get_id()
#            #else:
#            #    search_code = my.parent.get_code()

            if my.use_parent == 'true':
                parent_process = my.parent_processes[idx]
                if has_process:
                    key = "%s|%s|%s" % (search_type, search_code, parent_process)
                else:
                    key = "%s|%s|publish" % (search_type, search_code)
            else:
                key = "%s|%s|publish" % (search_type, search_code)
        else: #MTM Moved else down here to deal with our custom setup
            key = "%s|%s" % (my.parent.get_search_type(), my.parent.get_id())
        notes2 = None
        if my.try_tree:
            notes2 = my.notes_dict.get(my.sobject.get_value('code'))
        notes = my.notes_dict.get(key)
        if notes2 and notes:
            for n2 in notes2:
                if n2 not in notes:
                    notes.append(n2)
        if not notes:
            notes = notes2


        """
        use_parent = my.use_parent in ['true', True]
        has_process = my.sobject.has_value('process')

        if has_process and use_parent:
            process = my.parent_processes[idx]
        else:
            process = "publish"

        if my.parent:
            search_type = my.parent.get_search_type()
            # Note that this function falls back to id if no code exists
            search_code = my.parent.get_code()

            if process:
                key = "%s|%s|%s" % (search_type, search_code, process)
            else:
                key = "%s|%s" % (search_type, search_code)
        else:
            key = ''


        notes = my.notes_dict.get(key)
        if not notes:
            search_type = my.parent.get_search_type()
            search_code = my.parent.get_id()
            if process:
                key = "%s|%s|%s" % (search_type, search_code, process)
            else:
                key = "%s|%s" % (search_type, search_code)

        """

        #notes = my.notes_dict.get(key) #MTM
        if not notes:
            notes = []





        # not very efficient, but filter notes afterwards
        security = Environment.get_security()
        project_code = Project.get_project_code()
        allowed = []
        for note in notes:
            process = note.get_value("process")
            keys = [
                    {"process": process},
                    {"process": "*"},
                    {"process": process, "project": project_code},
                    {"process": "*", "project": project_code}
            ]
            if security.check_access("process", keys, "allow", default="deny"):
                allowed.append(note)

        return allowed



    def get_menu_wdg(my, top):
        '''Get the menu setup so the caller can place it outside this DiscussionWdg 
           with the top element passed in'''
        edit_wdg = DiscussionEditWdg()
        my.menu = edit_wdg.get_menu()

        # extra js_action on mouseover to assign the search key of the note to hidden input
        js_action ='''
           var sk_input = menu_top.getElement('.spt_note_action_sk');
           var note_top = bvr.src_el;
           sk_input.value = note_top.getAttribute('note_search_key');
            '''

        my.menu.set_activator_over(top, 'spt_note', js_action=js_action)
        my.menu.set_activator_out(top, 'spt_discussion_top')
        return edit_wdg
    
    def load_js(my, ele):
        '''add load bvr to the widget at startup or refresh'''
        ele.add_behavior({'type': 'load',
            'cbjs_action': my.get_onload_js()})
        my._load_js = True

    def get_display(my):
        import datetime
        #MTM DOWN TO....
        right_now = my.get_time_date_dict(my.make_timestamp())
        login = Environment.get_user_name()
        my.login = login
        grp_str = ''
        if login:
            from pyasm.security import LoginGroup
            groups = LoginGroup.get_group_names() #MTM Added this
            for grp in groups: #MTM Added this
                if grp_str == '': #MTM Added this
                    grp_str = grp #MTM Added this
                else: #MTM Added this
                    grp_str = '%s|%s' % (grp_str, grp) #MTM Added this
        #MTM .... HERE
       
        my.is_refresh = my.kwargs.get("is_refresh")

        my.hidden = my.kwargs.get('hidden') == True 
        

        my.show_border = my.kwargs.get("show_border")
        if my.show_border in ['false', False]:
            my.show_border = False
        else:
            my.show_border = True


        my.contexts_checked = my.kwargs.get("contexts_checked")
        if my.contexts_checked in ['false', False]:
            my.contexts_checked = False
        else:
            my.contexts_checked = True


        # explicitly set the contexts
        my.contexts = my.kwargs.get("context")

        # this should be maintained as a list
        if not my.contexts:
            my.contexts = []
        if my.contexts:
            my.contexts = my.contexts.split(",")
            # remove any spaces
            my.contexts = [x.strip() for x in my.contexts]
       
        
        # show context header
        my.show_context_header = my.kwargs.get("show_context_header")
        if my.show_context_header in ['true', True]:
            my.show_context_header = True
        else:
            my.show_context_header = False

            

        # show the number of notes that will start open.  default is 0
        my.default_num_notes = my.kwargs.get("default_num_notes")
        if my.default_num_notes:
            my.default_num_notes = int(my.default_num_notes)
        else:
            my.default_num_notes = 0

        show_fullscreen_button = my.kwargs.get("show_fullscreen_button")
        if show_fullscreen_button in ['true', True]:
            show_fullscreen_button = True
        else:
            show_fullscreen_button = False

        my.note_expandable = my.kwargs.get("note_expandable")
        
        my.note_format = my.kwargs.get("note_format")

        if my.note_format in ['', None]:
            my.note_format = 'compact'

        my.show_note_status = my.kwargs.get("show_note_status")
        if my.show_note_status in ['true', True]:
            my.show_note_status = True
            my.note_status_dict = ProdSetting.get_dict_by_key('note_status')
        else:
            my.show_note_status = False

        #my.default_contexts_open = my.kwargs.get("default_contexts_open")
        from pyasm.web import WebContainer
        web = WebContainer.get_web()
        my.default_contexts_open = web.get_form_values("default_contexts_open")
        if not my.default_contexts_open:
            my.default_contexts_open = my.kwargs.get("default_contexts_open")
        if not my.default_contexts_open:
            my.default_contexts_open = []


        if my.is_refresh =='true':
            top = Widget()
        else:
            top = DivWdg()
            if not my._load_js:
                my.load_js(top)
            
                if my.kwargs.get("add_behaviors") != False:
                    my.add_layout_behaviors(top, allow_email=my.allow_email)


            # add a refresh listener
            top.add_class("spt_discussion_top")
            my.set_as_panel(top)
            top.add_style("min-width: 300px")


            max_height = my.kwargs.get("max_height")
            if max_height:
                top.add_style("overflow: auto")
                top.add_style("max-height: %spx" % max_height)

        notes = my.get_notes()

        if my.use_parent == 'true' and not notes and not my.parent:
            sobj = my.parent
            if my.sobject.is_insert():
                return top
            if sobj:
                st_obj = sobj.get_search_type_obj()
                msg = 'Warning: The parent of this [%s] cannot be found. If this happens for every item, try not to set the display option [use_parent] to true.' % st_obj.get_title()
            else:
                msg = 'Warning: The parent cannot be found for this sObject. If this happens for every item, try not to set the display option [use_parent] to true.'
            top.add(msg)
            top.add_style("padding: 5px")
            return top

        if my.sobject.is_insert():
            return top

        code = my.parent.get_code()
       
        sobj = my.sobject
        has_process = my.sobject.has_value('process')
        has_context = my.sobject.has_value('context')
        if notes:
            expand_div = DivWdg()

            # FIXME: this is current broken because of the dialogs on notes
            show_fullscreen_button = False
            if show_fullscreen_button:
                top.add(expand_div)
                expand_div.add_class("spt_discussion_expand")
                #expand_div.add_style("float: right")
                expand_div.add_style("margin: -2px 3px 2px 3px")
                expand_div.add_style("margin-right: 3px")

                expand_wdg = IconButtonWdg(title="Expand in new tab", icon=IconWdg.ZOOM)
                expand_div.add(expand_wdg)

                expand_div.add_attr('code', code)
                expand_div.add_attr('search_key', my.parent.get_search_key())




        # This only shows up if there are no notes
        else:
            no_notes_div = DivWdg()
            top.add(no_notes_div)
            if my.show_border:
                no_notes_div.add_color("background", "background")
                no_notes_div.add_color("color", "color")
            no_notes_div.add_style("padding", "3px")

            #add_wdg = ActionButtonWdg(title="+", title2="-", tip='Add a new note', size='small', opacity=0.7)
            #no_notes_div.add(add_wdg)
            #add_wdg.add_style("float: left")
            #add_wdg.add_style("margin-top: -7px")
            #add_wdg.add_style("margin-right: -2px")
  
            add_class = my.get_note_class(my.hidden, 'spt_discussion_add') 
            #add_wdg.add_class(add_class)

            no_notes_msg = DivWdg()
            no_notes_msg.add_style("opacity: 0.5")
            no_notes_msg.add_style("min-height: 18px")
            no_notes_div.add(no_notes_msg)
            add_wdg = IconWdg("Add Note", "BS_PLUS")
            no_notes_msg.add(add_wdg)
            msg = "No notes. Click to add."
            no_notes_msg.add("<i> %s </i>" % _(msg))
            no_notes_div.add_style("font-size: 0.9em")
            no_notes_div.add_class("hand")

            no_notes_msg.add_class(add_class)

          
            # only pass in the context choices if has_process is true e.g. for Task and Snapshot notes
            if my.contexts:
                context_choices = my.contexts
            elif has_process and has_context:
                context_choices = [sobj.get_value('context')]
            else:
                context_choices = []

            process_choice = ''
            if my.process:
                process_choice = my.process
            elif has_process:
                process_choice = sobj.get_value('process')
            
            sk = my.parent.get_search_key(use_id=True)
            if isinstance(sk, unicode):
                sk = sk.encode('utf-8')
            
            kwargs = {
                    'search_key': sk,
                    'context': context_choices,
                    'process': process_choice,
                    'use_parent': my.use_parent,
                    'append_process': my.append_processes
            }


            note_dialog = DialogWdg(display=False)
            note_dialog.add_title("Add Note")
            note_dialog.add_style("overflow-y: auto")
            no_notes_div.add(note_dialog)
            note_dialog.set_as_activator(no_notes_msg, offset={'x':-5,'y':0})

            add_note_wdg = DivWdg()
            add_note_wdg.add_class("spt_add_note_container")
            add_note_wdg.add_attr("spt_kwargs", jsondumps(kwargs).replace('"',"'"))
            #no_notes_div.add(add_note_wdg)
            note_dialog.add(add_note_wdg)


            return top

        # calculate the number for each context
        my.c_new = {}
        my.orig_c_new = {}
        my.context_counts = {}
        my.context_codes = {}
        for note in notes:
            process = note.get_value("process")
            context = note.get_value("context")
            orig_process = process
            orig_context = context
            if my.chrono:
                process = my.chrono_name
                context = my.chrono_name
            count = my.context_counts.get(context)
            if count == None:
                count = 1
            else:
                count += 1 
            my.context_counts[context] = count
            if context not in my.c_new.keys():
                my.c_new[context] = 0
            if context not in my.context_codes.keys():
                my.context_codes[context] = []
            my.context_codes[context].append(note.get_value("code"))
#            if my.highlight:
#                seen_by = note.get_value("seen_by")
#                if login not in seen_by:
#                    my.c_new[context] = my.c_new[context] + 1
#                    if orig_context not in my.orig_c_new.keys():
#                        my.orig_c_new[orig_context] = 0
#                    my.orig_c_new[orig_context] = my.orig_c_new[orig_context] + 1
            if my.show_note_top or my.highlight:
                seen_by = note.get_value("seen_by")
                if login not in seen_by:
                    my.c_new[context] = my.c_new[context] + 1
                    if orig_context not in my.orig_c_new.keys():
                        my.orig_c_new[orig_context] = 0
                    my.orig_c_new[orig_context] = my.orig_c_new[orig_context] + 1

        if my.show_context_header:
            contexts = set()
            for note in notes:
                context = note.get_value("context")
                if my.chrono:
                    context = my.chrono_name
                contexts.add(context)
            contexts_div = DivWdg()
            contexts_div.add_color("color", "color")
            if my.show_border:
                contexts_div.add_border()
            top.add(contexts_div)
            for context in contexts:
                checkbox = CheckboxWdg("context")
                #if my.contexts_checked:
                checkbox.set_checked()
                checkbox.add_behavior( {
                'type': 'change',
                'context': context,
                'cbjs_action': '''

                var value = bvr.src_el.checked;
                var top = bvr.src_el.getParent(".spt_discussion_top");
                var contexts = top.getElements(".my_context");
                for (var i = 0; i < contexts.length; i++) {
                    if (contexts[i].getAttribute("my_context") == bvr.context) {
                        if (value == true) {
                            spt.show(contexts[i]);
                        }
                        else {
                            spt.hide(contexts[i]);
                        }
                    }
                }

                var notes = top.getElements(".spt_note");
                for (var i = 0; i < notes.length; i++) {
                    if (notes[i].getAttribute("my_context") == bvr.context) {
                        if (value == true) {
                            spt.show(notes[i]);
                        }
                        else {
                            spt.hide(notes[i]);
                        }

                    }
                }
 

                '''
                } )
                contexts_div.add(checkbox)
                contexts_div.add(context)
                contexts_div.add("&nbsp;"*3)
            

        # determines if each note in the context group is hidden
        show_context_notes = my.kwargs.get("show_context_notes")
        if show_context_notes in [True, "true"]:
            show_context_notes = True
        else:
            show_context_notes = False

        # go through every note and display
        last_context = None
        context_top = None
        context_count = 0
        note_content = None
        
        
        i = 0
        #for i, note in enumerate(notes):
        for note in notes:
            context = note.get_value("context")
            process = note.get_value("process")
            if my.chrono:
                context = my.chrono_name
                process = my.chrono_name
            if last_context == None or context != last_context:
                if context != 'client' or ('scheduling' in grp_str or 'client' in grp_str):
                    # organize by context
                    context_top = DivWdg()
                    context_top.add_class("spt_discussion_context_top")
                    context_top.add_class("my_context")
                    #context_top.add_class("hand")
                    context_top.add_attr("my_context", context.encode('utf-8'))
                    top.add(context_top)
    
                    if show_context_notes or context in my.default_contexts_open:
                        context_top.add_attr("spt_state", 'open')
                    else:
                        context_top.add_attr("spt_state", 'closed')
    
                    context_wdg = my.get_context_wdg(process, context, show_context_notes=show_context_notes)
                    last_context = context
                    context_top.add(context_wdg)
                    context_top.add_style("min-width: 300px")
                    # prefer my.process. if not set, use context 
                    #process = my.process
    
                    # NOTE: this is fine if just adding shot level notes, but when dealing with task based notes, it
                    # may not be appropriate
                    #if not process:
    
                    #    process = context
                    
                    #add_note_wdg = DiscussionAddNoteWdg(parent=my.parent,context=my.contexts, process=process, use_parent=my.use_parent)
                    if my.contexts:
                        context_choices = my.contexts
                    elif has_process and has_context:
                        context_choices = [sobj.get_value('context')]
                    else:
                        context_choices = []
    
                    process_choice = ''
                    if my.process:
                        process_choice = my.process
                    elif has_process:
                        process_choice = sobj.get_value('process')

                context_count = 0

                #if not my.contexts_checked or not my.show_context_header:
                #    context_top.add_style('display: none')

                #MTM down to....
                context_codes = '|'.join(my.context_codes[context])
                js_action = '''
                    var context = '%s';
                    var context_codes = '%s';
                    login = '%s';
                    var top = bvr.src_el.getParent(".spt_discussion_top");
                    ctx_bar = top.getElementById("ctx_" + context);
                    cb_str = ctx_bar.innerHTML;
                    if(cb_str.indexOf('NEW') != -1){
                        var ctx_top = top.getParent(".ctx_counter");
                        var ctx_nums = ctx_top.getElementsByClassName('ctx_nums');
                        for(var r = 0; r < ctx_nums.length; r++){
                            ctx_nums[r].innerHTML = ''
                        }  
                        var notes = top.getElements(".spt_note");
                        var server = TacticServerStub.get();
                        var note_objs = server.eval("@SOBJECT(sthpw/note['code','in','" + context_codes + "'])"); 
                        var ts = Math.round(new Date().getTime() / 1000);
                        var updated_one = false;
                        var codes_to_update = '';
                        for(var r = 0; r < note_objs.length; r++){
                            tnote = note_objs[r];
                            seen_by = tnote.seen_by;
                            if(seen_by.indexOf(login) == -1){
                                //new_seen_by = seen_by + '[ ' + login + ' ,' + ts + ']';
                                //Want to send this to UpdateNotesSeenByCmd so it will go faster
                                //server.update(server.build_search_key('sthpw/note', tnote.code), {'seen_by': new_seen_by}); 
                                updated_one = true;
                                if(codes_to_update == ''){
                                    codes_to_update = tnote.code;
                                }else{
                                    codes_to_update = codes_to_update + ',' + tnote.code;
                                } 
                            }
                        }
                        if(updated_one){
                            server.execute_cmd("manual_updaters.UpdateNotesSeenByCmd", {'codes_to_update': codes_to_update, 'login': login, 'timestamp': ts});
                            nbrs = cb_str.split(') ')[0];
                            new_cb_str = nbrs + ")";
                            ctx_bar.innerHTML = new_cb_str;
                        }
                    }
                    ''' % (context, context_codes, login)
                #Here....MTM

               
                note_dialog = DialogWdg(display=False)
                note_dialog.add_title(context)
                note_dialog.add_style("overflow-y: auto")
                context_top.add(note_dialog)
                if my.highlight:
                    note_dialog.set_as_activator(context_wdg, offset={'x':0,'y':0}, extra_js=js_action)
                else:
                    note_dialog.set_as_activator(context_wdg, offset={'x':0,'y':0})


                show_add = my.kwargs.get("show_add")
                if show_add not in ['false', False]:

                    shelf_wdg = DivWdg()
                    note_dialog.add(shelf_wdg)
                    shelf_wdg.add_style("height: 36px")
                    shelf_wdg.add_color("background", "background3")

                    add_wdg = ActionButtonWdg(title="+", title2="-", tip='Add a new note', size='small', opacity=0.7)
                    shelf_wdg.add(add_wdg)
                    add_wdg.add_style("float: right")
                    shelf_wdg.add_style("padding-top: 3px")

                    add_wdg.add_attr("spt_process", process)
                    add_wdg.add_attr("spt_context", context)
                    add_class = my.get_note_class(my.hidden, 'spt_discussion_add') 
                    add_wdg.add_class(add_class)

                    sk = my.parent.get_search_key(use_id=True)
                    if isinstance(sk, unicode):
                        sk = sk.encode('utf-8')
                    kwargs = {
                            'search_key': sk,
                            'context': context_choices,
                            'process': process_choice,
                            'use_parent': my.use_parent,
                            'append_process': my.append_processes
                    }

                    add_note_wdg = DivWdg()
                    add_note_wdg.add_class("spt_add_note_container")
                    add_note_wdg.add_attr("spt_kwargs", jsondumps(kwargs).replace('"',"'"))
                    note_dialog.add(add_note_wdg)


                note_content = DivWdg()
                note_dialog.add(note_content)
                note_content.add_style("max-height: 500px")
                note_content.add_style("overflow-y: auto")
                note_content.add_style("overflow-x: hidden")
                """
                note_content.add_behavior( {
                    'type': 'load',
                    'cbjs_action': '''
                    var win_size = $(window).getSize();
                    bvr.src_el.setStyle("max-height", win_size.y*0.75);
                    '''
                } )
                """





            if my.default_num_notes == -1:
                note_hidden = True
            elif context_count >= my.default_num_notes:
                note_hidden = True
            else:
                note_hidden = False

            note_wdg = my.get_note_wdg(note, show_context_notes=show_context_notes, note_hidden=note_hidden)
            if i % 2 == 0:
                note_wdg.add_color("background", "background", -3)
            else:
                note_wdg.add_color("background", "background", -6)
            note_wdg.add_style("border-style: solid")
            note_wdg.add_style("border-width: 0 0 1px 0")
            note_wdg.add_style("border-color: %s" % note_wdg.get_color("table_border"))

            note_content.add(note_wdg)
            note_wdg.add_style("width: 395px")

            #top.add(note_wdg)

            context_count += 1
            i = i + 1
        #MTM DOWN
        ctbl = Table()
        ctbl.add_attr('class','ctx_counter')
        if my.show_new_contexts and my.show_note_top:
            for k in my.orig_c_new.keys():
                val = my.orig_c_new[k]
                if val > 0:
                    ctbl.add_row()
                    if my.highlight:
                        c1 = ctbl.add_cell('''<font color="#FF0000"><i>NEW: %s (%s)</i></font>''' % (k, val))
                    else:
                        c1 = ctbl.add_cell('''%s (%s)''' % (k, val))
                    c1.add_attr('class','ctx_nums')
                    c1.add_style('font-size: 9px;')
        ctbl.add_row()
        ctbl.add_cell(top)  
        #MTM to here, plus line below
        return ctbl

    def get_context_wdg(my, process, context, show_context_notes=True):
        ''' this is drawn per process/context group of notes'''
        div = DivWdg()
        div.add_class("hand")

        swap = SwapDisplayWdg()
        div.add(swap)
        swap.add_style("float: left")
        swap.add_style("margin-top: -2")
        swap.add_style("margin-left: -5")

        if show_context_notes or context in my.default_contexts_open:
            swap.set_off()

        # this part doesn't need swap script 
        js_action = '''
                var context = '%s';
                var top = bvr.src_el.getParent(".spt_discussion_top");
                var notes = top.getElements(".spt_note");
                for (var i = 0; i < notes.length; i++) {
                    if (context != notes[i].getAttribute("my_context") ) {
                        continue;
                    }
                    spt.toggle_show_hide(notes[i]);

                }
                
                var context_el = bvr.src_el.getParent(".my_context");
                var state = context_el.getAttribute("spt_state");
                if (state == 'open')
                    state = 'closed';
                else
                    state = 'open';
                context_el.setAttribute("spt_state", state);
                ''' %context

        bvr = {
                'type': 'click_up',
                'cbjs_action':  '''
                %s
                %s
                '''%(js_action, swap.get_swap_script())
                }

        swap.add_action_script(js_action)
        
        div.add_behavior(bvr)

        show_add = my.kwargs.get("show_add")
        if show_add not in ['false', False]:
            add_wdg = ActionButtonWdg(title="+", title2="-", tip='Add a new note', size='small', opacity=0.7)
            div.add(add_wdg)
            add_wdg.add_style("float: right")
            add_wdg.add_style("margin-top: -7px")
            add_wdg.add_style("margin-right: -3px")
            #dialog.set_as_activator(add_wdg)

            add_wdg.add_attr("spt_process", process)
            add_wdg.add_attr("spt_context", context)
       

        div.add_color("color", "color")
        div.add_style("padding", "4px")
        div.add_color("background", "background", -5, -5)
        div.add_style("height", "15px")
        div.add_style("font-weight", "bold")
        #div.add_style("margin-bottom", "-1px")
        div.add_style("border-width: 0px 0px 1px 0px")
        div.add_style("border-style: solid")
        div.add_color("border-color", "table_border")
        if not context:
            context = '<i>(no context)</i>'
        div.add(context)

        count_div = SpanWdg()
        div.add(count_div)
        count = my.context_counts.get(context)
        count_div.add(" (%s)" % count)
        count_div.add_style("font-weight: normal")
        count_div.add_style("font-size: 1.0em")
        count_div.add_style("font-style: italic")


        return div



    def get_context_wdg(my, process, context, show_context_notes=True):
        ''' this is drawn per process/context group of notes'''
        div = DivWdg()
        div.add_class("hand")


        icon_div = SpanWdg()
        div.add(icon_div)
        icon_div.add_border()
        icon_div.add_style("width: 16px")
        icon_div.add_style("height: 16px")
        icon_div.add_style("overflow: hidden")
        icon_div.add_style("margin-right: 5px")
        icon_div.add_style("float: left")

        icon = IconWdg( "View", IconWdg.ARROWHEAD_DARK_DOWN)
        icon_div.add(icon)
        context_codes = '|'.join(my.context_codes[context]) #MTM



        div.add_color("color", "color")
        div.add_style("padding", "5px")
        div.add_color("background", "background", -5, -5)
        div.add_style("height", "15px")
        div.add_style("font-weight", "bold")
        #div.add_style("margin-bottom", "-1px")
        div.add_style("border-width: 0px 0px 1px 0px")
        div.add_style("border-style: solid")
        div.add_color("border-color", "table_border")
        if not context:
            display_context = '<i>(no context)</i>'
        elif context == "publish":
            display_context = "Notes"
        else:
            display_context = context
        div.add(display_context)

        count_div = SpanWdg()
        count_div.add_attr('id','ctx_%s' % context) #MTM
        div.add(count_div)
        count = my.context_counts.get(context)
        new_str = '' #MTM
        if my.c_new[context] > 0 and my.highlight: #MTM
            new_str = '<font color="#FF000"><b>%s NEW</b></font>' % (my.c_new[context]) #MTM
        count_div.add(" (%s) %s" % (count, new_str)) #MTM
        count_div.add_style("font-weight: normal")
        count_div.add_style("font-size: 1.0em")
        count_div.add_style("font-style: italic")

        return div










    def get_note_wdg(my, note, show_context_notes=True, note_hidden=False):
        context = note.get_value("context")
        orig_context = context # MTM
        if my.chrono: # MTM
            context = my.chrono_name # MTM
        note_sk = note.get_search_key() # MTM

        mode = "dialog"

        div = DivWdg()
        div.add_class("spt_note")
        div.add_attr('note_search_key', note.get_search_key())


        if mode != 'dialog' and not show_context_notes and context not in my.default_contexts_open:
            div.add_style("display: none")

        note_value = note.get_value("note") 
        login = note.get_value("login")
        date = note.get_value("timestamp")
        context = note.get_value("context")
        seen_by = note.get_value('seen_by') #MTM
        if my.chrono: #MTM
            context = my.chrono_name #MTM

        div.add_attr("my_context", context.encode("UTF-8"))


        content = Table(css='minimal')
        content.add_style("width: 95%")
        content.add_color("color", "color")
        content.add_style("padding: 4px")

        div.add(content)
        content.add_class("spt_note_top")


        content.add_row()
        td = content.add_cell()


        icon = IconWdg("Note", "BS_PENCIL")
        #td.add(icon)
        icon.add_style("float: left")
        icon.add_style("margin: 5px")
        title = DivWdg()
        title.add_class("spt_note_header")
        title.add_style("margin: 5px 12px")
        title.add_style("font-weight: bold")

        tbody = content.add_tbody()

        if my.note_expandable in ['true', True]:
            title.add_class("hand")
            swap = SwapDisplayWdg.get_triangle_wdg()
            if note_hidden not in ['true', True]:
                swap.set_off()
            SwapDisplayWdg.create_swap_title(title, swap, tbody)
            title.add(swap)
            
        #else:
            #title.add(tbody)


        date_obj = dateutil.parser.parse(date)
        date_obj = SPTDate.convert_to_local(date_obj)
        display_date_full = date_obj.strftime("%b %d, %Y %H:%M")
        display_date = date_obj.strftime("%b %d - %H:%M")

        if my.note_expandable in ['true', True]:
            if len(note_value) > 50:
                short_note = "%s ..." % note_value[:48]
            else:    
                short_note = note_value
                
        else: 
            # show the entire note
            #short_note = WikiUtil().convert(note_value)
            short_note = ''
            
           
        if short_note:
            title.add("%s - %s" % (login, short_note) )
        else:
            title.add("<b style='font-size: 1.1em'>%s</b>" % (login) )


        title.add("<div style='float: right'>%s</div>" % display_date)
        title.add_attr("title", display_date_full)

        if my.show_note_status:
            status = note.get_value('status')
            status_label = my.note_status_dict.get(status)
            if status_label:
                title.add (' - %s ' %status_label)


        td.add(title)

        key = note.get_search_key()
        attachments = my.attachments.get(key)
        if attachments:
            bubble = 'View Attachments'
            if len(attachments) > 1:
                bubble = '%s (%s)'%(bubble, len(attachments))
            btn = IconButtonWdg(title=bubble, icon=IconWdg.ATTACHMENT)
            title.add("&nbsp;");
            btn.add_style("float: right");
            title.add(btn)
            btn.add_class("spt_note_attachment")

            # get the codes to the attachments
            attachment_codes = []
            for attachment in attachments:
                attachment_codes.append( attachment.get_code() )
            btn.add_attr("spt_note_attachment_codes", "|".join(attachment_codes) )


        tbody.add_class("spt_note_content")

        if mode == "dialog":
            tbody.add_style("display", "")
        elif note_hidden in ['true', True] and my.note_expandable in ['true', True]:
            tbody.add_style("display: none")
        else:
            tbody.add_style("display", "")
        
        # don't draw the detailed attachment and user info
        '''
        if my.note_format == 'compact':
            content.close_tbody()
            return div
        '''
        content.add_row()
        if my.note_format == 'full':
            left = content.add_cell()
            left.add_style("padding: 10px")
            left.add_style("width: 150px")
            left.add_style("min-height: 100px")
            left.add_style("vertical-align: top")

            if not login:
                login = "-- No User --"
                left.add(login)
            else:
                '''
                from pyasm.security import Login
                from pyasm.widget import ThumbWdg
                '''
                login_sobj = Login.get_by_code(login)

                thumb = ThumbWdg()
                thumb.set_icon_size("60")
                if login_sobj:
                    thumb.set_sobject(login_sobj)
                    left.add(thumb)
                    left.add("<br/>")
                    left.add_style("font-size: 1.0em")

                    #left.add("%s</br>" % login) #MTM was gone in download from 4_15
                    name = "%s %s" % (login_sobj.get_value("first_name"), login_sobj.get_value("last_name") )
                    left.add("%s</br>" % name)
                    left.add("%s</br>" % login_sobj.get_value("email"))





        right = content.add_cell()
        right.add_style("vertical-align: top")
        right.add_style("padding: 10px 30px")

        context = note.get_value("context")
        #MTM DOWN TO....
        if my.chrono:
            context = my.chrono_name
        from uploader import CustomHTML5UploadButtonWdg 
        #files_butt = CustomHTML5UploadButtonWdg(processes="note_attachment",sk=note_sk,name="Files")
        files_butt = CustomHTML5UploadButtonWdg(processes="publish",sk=note_sk,name="Files")

        if my.highlight:
            if my.login not in seen_by:
                orig_context = '<font color="#FF0000">%s</font>' % orig_context
        context_div = DivWdg() #MTM - the following 5 lines were in 3.9 and were uncommented
        context_div.add(orig_context)
        context_div.add_style("padding: 5px")
        context_div.add_style("font-size: 1.1em")
        context_div.add_style("font-weight: bold")
        cftbl = Table() # MTM - these 5 lines were uncommented in 3.9
        cftbl.add_row()
        cftbl.add_cell(context_div)
        cftbl.add_cell(files_butt)
        right.add(cftbl)
        #MTM ...HERE

        right.add( WikiUtil().convert(note_value) )


        attached_div = DivWdg()
        attached_div.add_style("margin-top: 10px")
        snapshots = attachments
        if snapshots:
            attached_div.add("<hr/>Attachments: %s<br/>" % len(snapshots) )

            for snapshot in snapshots:
                thumb_div = DivWdg()
                attached_div.add(thumb_div)
                thumb_div.add_style("float: left")

                thumb = ThumbWdg()
                thumb.set_option('detail','false')
                thumb_div.add(thumb)
                thumb.set_icon_size(60)
                thumb.set_sobject(snapshot)

        right.add(attached_div)

        content.close_tbody()

	div.add_style("word-wrap: break-word") #MTM
	div.add_style("word-break: break-all") #MTM
        return div




class DiscussionAddNoteWdg(BaseRefreshWdg):
    '''This widget draws the UI that user clicks to add note'''
        
    def add_style(my, name, value=None):
        my.top.add_style(name, value)


    def init(my):
        my.hidden = my.kwargs.get("hidden")
        my.append_processes = my.kwargs.get("append_process")
        if my.append_processes:
            my.append_processes = my.append_processes.split(",")
            # remove any spaces
            my.append_processes = [x.strip() for x in my.append_processes if x]

        my.upload_id = my.kwargs.get("upload_id")
        
        my.allow_email = my.kwargs.get("allow_email") not in ['false', False]
        

    def get_display(my):
        from tactic_client_lib import TacticServerStub # MTM
        server = TacticServerStub.get() # MTM
        login = Environment.get_user_name()
        grp_str = ''
        if login:
            from pyasm.security import LoginGroup
            groups = LoginGroup.get_group_names() #MTM Added this
            for grp in groups: #MTM Added this
                if grp_str == '': #MTM Added this
                    grp_str = grp #MTM Added this
                else: #MTM Added this
                    grp_str = '%s|%s' % (grp_str, grp) #MTM Added this
        preppend = ''
        if 'preppend' in my.kwargs.keys():
            preppend = my.kwargs.get('preppend')
        my.use_parent = my.kwargs.get("use_parent")
        parent = my.kwargs.get("parent")
        if not parent:
            search_key = my.kwargs.get("search_key")
            parent = Search.get_by_search_key(search_key)
        elif isinstance(parent, basestring):
            search_key = parent
            parent = Search.get_by_search_key(parent)
        search_type = parent.get_search_type() # MTM
        parent_code = parent.get_code() #MTM
        # MTM Logic that needs to be implemented: Save context as project, wo pair to the title, only if being added to a proj or wo 
        solid_ctx = '' # MTM
        solid_bool = False # MTM
        wo = None # MTM
        proj = None # MTM
        if 'twog/work_order' in search_type:   #MTM WIP...
            wo = server.eval("@SOBJECT(twog/work_order['code','%s'])" % parent_code)
            if wo:
                wo = wo[0]
                solid_bool = True
                proj = server.eval("@SOBJECT(twog/proj['code','%s'])" % wo.get('proj_code'))
                if proj:
                    proj = proj[0]
        elif 'twog/proj' in search_type:
            proj = server.eval("@SOBJECT(twog/proj['code','%s'])" % parent_code)
            if proj:
                proj = proj[0]
                solid_bool = True
        if solid_bool:
            if proj and not wo:
                solid_ctx = proj.get('process')
            if wo and proj:
                solid_ctx = '%s:%s' % (proj.get('process'), wo.get('process')) 
            if wo and not proj:
                solid_ctx = wo.get('process')
       # MTM WIP END



        # explicitly set the contexts
        my.contexts = my.kwargs.get("context")
        # need the process to predict the notification to and cc
        my.process = my.kwargs.get('process')
        my.append_contexts = my.get_option("append_context") #MTM, possibly a bad (for sure unused) 
        my.override_processes = my.get_option("override_processes")

      
        content_div = my.top

        my.set_as_panel(content_div)
        content_div.add_class("spt_discussion_add_note")

        display = my.kwargs.get("display")
        if not display:
            display = "none"
        content_div.add_style("display: %s" % display)

        content_div.add_color("background", "background")
        content_div.add_color("color", "color")
        content_div.add_style("padding: 10px")
        #content_div.add_border(style="solid")
        content_div.add_class("spt_add_note_top")

        search_key_hidden = HiddenWdg("search_key")
        search_key_hidden.set_value(parent.get_search_key())
        content_div.add(search_key_hidden)



        #if my.contexts:
        #    process_names = my.contexts
        
        if my.process:
            process_names = [my.process]
        else:
            pipeline_code = parent.get_value("pipeline_code", no_exception=True)
            if pipeline_code:
                pipeline = Pipeline.get_by_code(pipeline_code)
                if pipeline:
                    process_names = pipeline.get_process_names()
                    if not process_names:
                        process_names = ["publish"]
                else:
                    process_names = ["publish"] 
            else:
                process_names = ["publish"]

        if my.append_processes:
            process_names.extend(my.append_processes)

        security = Environment.get_security()
        project_code = Project.get_project_code()
        allowed = []

        for process in process_names:
            keys = [
                    {"process": process},
                    {"process": "*"},
                    {"process": process, "project": project_code},
                    {"process": "*", "project": project_code}
            ]
            if security.check_access("process", keys, "allow", default="deny"):
                allowed.append(process)
        process_names = allowed

        easy_st = search_type.split('?')[0] # MTM
        context_values = ProdSetting.get_value_by_key('%s_note_contexts' % easy_st) # MTM
        is_scheduler = False
        if 'scheduling' in grp_str:
            is_scheduler = True
        if easy_st in ['twog/order','twog/work_order','twog/equipment_used']: # MTM
            process_names = []
            if 'client' not in grp_str: 
                process_names = context_values.split('|')#MTM 
            if is_scheduler or 'client' in grp_str:
                process_names.append('client')
        if easy_st == 'twog/title' and is_scheduler:
            process_names.append('client')
            

        if not process_names:
            content_div.add("<i>You do not have permission to add notes here.</i>")
            return content_div

        from tactic.ui.app import HelpButtonWdg
        help_button = HelpButtonWdg(alias="notes-widget")
        content_div.add(help_button)
        help_button.add_style("float: right")
        help_button.add_style("margin-top: -5px")
        #MTM DOWN TO ..
        if my.override_processes not in [None,'']:
            process_names = []
            op_s = my.override_processes.split('|')
            for oper in op_s:
                process_names.append(oper)
            if my.process not in [None,'']:
                process_names.append(my.process)
        #MTM...HERE
        # prevent ppl from defining contexts directly when there is nothing defined for process, aka, publish
        
        if process_names == ["publish"]:
            hidden = HiddenWdg("add_process", 'publish')
            #hidden.set_value("publish")
            content_div.add(hidden)
            if my.contexts:
                content_div.add("Warning: You should define %s in process display option. 'publish' will override." % my.contexts)
        
            # context is optional, only drawn if it's different from process
        elif len(process_names) == 1:
            wdg_label = "For Process:"
            span = SpanWdg(wdg_label)
            span.add_style('padding-right: 4px')
            content_div.add(span)

            hidden = HiddenWdg("add_process")
            hidden.set_value(process_names[0])
            content_div.add(hidden)
            content_div.add("<b>%s</b>" % process_names[0])
        else:
            wdg_label = "For Process:"
            span = SpanWdg(wdg_label)
            span.add_style('padding-right: 4px')
            content_div.add(span)

            process_select = SelectWdg("add_process")
            process_select.add_class("spt_add_note_process")
            process_select.set_option("values", process_names)
            if my.process not in [None,'']: #MTM carried over from 3.9
                process_select.set_value(my.process) #MTM carried over from 3.9
            content_div.add(process_select)


        # add the context label if it is different from process in use_parent mode
        # this is a special case where we explicitly use processs/context for note
        if my.use_parent =='true' and my.contexts:
            hidden =HiddenWdg("add_context")
            hidden.set_value(my.contexts[0])
            content_div.add(hidden)
            if my.contexts[0] != my.process:
                context_span = SpanWdg(my.contexts[0], css='small')
                content_div.add(context_span)

        content_div.add("<br/>")


        content_div.add("<br/>Note:<br/>")
        text = TextAreaWdg("note")
        text.add_style("width: 100%")
        text.add_style("height: 100px")
        content_div.add(text)

        content_div.add("<br/>"*2)


        #add_button = ProdIconButtonWdg("Submit Note")
        add_button = ActionButtonWdg(title="Submit", tip='Submit information to create a new note')
        content_div.add(add_button)
        add_button.add_style("float: right")

        submit_class = DiscussionWdg.get_note_class(my.hidden, 'spt_discussion_submit') 
        add_button.add_class(submit_class)


        # attachments
        attachment_div = DivWdg()
        content_div.add(attachment_div)
        attachment_div.add_class("spt_attachment_top")

       
        from tactic.ui.input import UploadButtonWdg 
        on_complete = '''
       
        var files = spt.html5upload.get_files(); 
      
       
        var html = '';
        var file_names = [];
        for (var i = 0; i < files.length; i++) {
            file_names.push(files[i].name);
            html += files[i].name + '<br/>';
        }
        var top = bvr.src_el.getParent(".spt_attachment_top")
        var list = top.getElement(".spt_attachment_list");

        list.innerHTML = html;
      
        top.files = file_names;

       
        spt.app_busy.hide();
        '''
        table_upload_id = my.upload_id
      

        upload_init = ''' 
        var server = TacticServerStub.get();
        var ticket_key = server.start({title: 'New Note'});
        var top = bvr.src_el.getParent(".spt_attachment_top");
        top.setAttribute('ticket_key', ticket_key);
        upload_file_kwargs['ticket'] = ticket_key;
      
       
        '''

      

        browse_button = UploadButtonWdg(title="Attach File", tip='Browse for files to attach to this note', on_complete=on_complete,\
                upload_init=upload_init, multiple='true', upload_id=table_upload_id) 
        attachment_div.add(browse_button)
        #browse_button.add_style("float: left")


        attach_list = DivWdg()
        attach_list.add_style('margin-top: 8px')
        attachment_div.add(HtmlElement.br(2))
        attachment_div.add(attach_list)
        attach_list.add_class("spt_attachment_list")


        attachment_div.add(HtmlElement.br())

        if not my.allow_email:
            return content_div

        swap = SwapDisplayWdg()
        content_div.add(swap)
        swap.add_style("float: left")
        title = DivWdg("Mail Options")
        title.add_style("margin: 2px 0px 0px -2px")
        content_div.add(title)

        mail_div = DivWdg()
        SwapDisplayWdg.create_swap_title(title, swap, mail_div)
        #MTM DOWN TO ....
        files_div = DivWdg()
        files_div.add_attr('search_key',parent.get_search_key())
        files_div.add_attr('transaction_ticket',parent.get_search_key())
        files_div.add_attr('id','files_div')
        files_div.add(' ')

        content_div.add("<br/>")
        content_div.add(files_div)
        #MTM...HERE
        content_div.add("<br/>")
        content_div.add(mail_div)
        mail_div.add_class("spt_discussion_mail")
        #mail_div.add_style("display: none")
        mail_div.add("Mail will be sent to:<br/>")

        from pyasm.command import EmailHandler

        # there could be multiple.. so this is not always accurate
        search = Search("sthpw/notification")
        search.add_filter("process", process_names[0])
        search.add_filter("event", "insert|sthpw/note")
        notification = search.get_sobject()
        if notification:
            handler = EmailHandler(notification, None, None, None)
            to = handler.get_mail_users("mail_to")
            cc = handler.get_mail_users("mail_cc")
            to_emails = []
            cc_emails = []
            for x in to:
                if isinstance(x, SObject):
                    to_emails.append(x.get_value('email'))
                else:
                    to_emails.append(x)
            for x in cc:
                if isinstance(x, SObject):
                    cc_emails.append(x.get_value('email'))
                else:
                    cc_emails.append(x)

           
            mail_div.add("To: %s<br/>" % ",".join(to_emails))
            mail_div.add("Cc: %s<br/>" % ",".join(cc_emails))


        mail_div.add(HtmlElement.br())
        # mail cc and bcc
        mail_div.add("Extra list of email addresses - comma separated:")



        table = Table()
        table.add_color("color", "color")
        mail_div.add(table)
        #MTM ADDED ALL THE WAY DOWN TO .....
        #logins = server.eval("@SOBJECT(sthpw/login)")
        int_logins = server.eval("@SOBJECT(sthpw/login['location','internal']['license_type','user'])")
        inhousers = SelectWdg('inhousers')
        inhousers.append_option('--Select--','')

        
        group_internals = ProdSetting.get_value_by_key('internal_group_emails') # MTM
        if group_internals not in [None,'']:
            gis = group_internals.split('|')
            for gi in gis:
                gie = gi.split('->')
                slbl = gie[0]
                semail = gie[1]
                inhousers.append_option(slbl, semail)

        for logger in int_logins:
            inhousers.append_option('%s %s' % (logger.get('first_name'), logger.get('last_name')), logger.get('email'))
        if is_scheduler:
            ext_logins = server.eval("@SOBJECT(sthpw/login['location','external'])")
            externals = SelectWdg('externals')
            externals.append_option('--Select--','')
            for logger in ext_logins:
                externals.append_option('%s %s' % (logger.get('first_name'), logger.get('last_name')), logger.get('email'))
        table.add_row()
        table.add_cell('Internal: ')
        table.add_cell(inhousers)
        if is_scheduler:
            table.add_row()
            table.add_cell('External: ')
            table.add_cell(externals)
        sel_behavior = {'css_class': 'sel_change', 'type': 'change', 'cbjs_action': '''        
             try{
                   //var top_el = spt.api.get_parent(bvr.src_el, '.spt_add_note_top');
                   var top_el = spt.api.get_parent(bvr.src_el, '.spt_discussion_mail');
                   inputs = top_el.getElementsByTagName('input');
                   selval = bvr.src_el.value;
                   if(selval != '' && selval != null){
                           cc = '';
                           for(var r = 0; r < inputs.length; r++){
                               if(inputs[r].getAttribute('name') == 'mail_cc'){
                                   cc = inputs[r];
                               }
                           }
                           cc_val = cc.value;
                           if(cc_val == '' || cc_val == null){
                               cc.value = selval;
                           }else{
                               cc.value = cc_val + ';' + selval;
                           }
                   }
                    
                }
                catch(err){
                          spt.app_busy.hide();
                          alert(err);
                }
         '''}
        inhousers.add_behavior(sel_behavior)
        if is_scheduler:
            externals.add_behavior(sel_behavior)



        # ...HERE. MTM

        # CC
        table.add_row()
        table.add_cell("Cc: ")
        text = TextWdg("mail_cc")
        text.add_style("width: 250px")
        table.add_cell(text)

        table.add_row_cell()

        # BCC 
        table.add_row()
        table.add_cell("Bcc: ")
        text = TextWdg("mail_bcc")
        text.add_style("width: 250px")
        table.add_cell(text)

        return content_div




class DiscussionAddNoteCmd(Command):
    ''' this is the UI to add note when someone clicks on the + button. It does not contain the + button'''
    def get_title(my):
        return "Added a note"

    def execute(my):
        search_key = my.kwargs.get("search_key")
        sobject = Search.get_by_search_key(search_key)

        ticket = my.kwargs.get('ticket')
        note = my.kwargs.get("note")
        mail_cc = my.kwargs.get("mail_cc")
        mail_bcc = my.kwargs.get("mail_bcc")
        files = my.kwargs.get("files")
        if mail_cc:
            mail_cc = mail_cc.split(',')
        else:
            mail_cc = []
        if mail_bcc:
            mail_bcc = mail_bcc.split(',')
        else:
            mail_bcc = []
        process = my.kwargs.get("process")
        context = my.kwargs.get("context")
        preppend = ''
        if 'preppend' in my.kwargs.keys():#MTM
            preppend = my.kwargs.get('preppend')#MTM
        if preppend not in [None,''] and 'client' not in context and 'client' not in process:#MTM
            note = '%s\n%s' % (preppend, note)#MTM
        elif preppend not in [None,''] and 'client_services' in context or 'client_services' in process:
            note = '%s\n%s' % (preppend, note)#MTM
        if not context:
            context = process

        from pyasm.biz import Note
        #MTM DOWN TO ...
        if files not in [None,'',[],{}]:
            note = '%s\nHASATTACHEDFILES:%sMTMCOUNT' % (note, len(files))
        note = Note.create(sobject, note, context=context, process=process, addressed_to=mail_cc)
        #MTM HERE
        subject = 'Added Note'
        message = 'The following note has been added for [%s] under "%s":\n%s '%(sobject.get_code(), process, note.get_value('note')) #MTM added process/context part
        project_code = Project.get_project_code()
        users = []
        users.extend(mail_cc)
        users.extend(mail_bcc)
        # MTM Turned these emails off. They are crappy and not formatted well.
        #if len(users) > 0:
        #    EmailTrigger2.add_notification(users, subject, message, project_code)
        #    EmailTrigger2.send([],[],[], subject, message, cc_emails=mail_cc,bcc_emails=mail_bcc)


        

        from pyasm.checkin import FileCheckin
        files = my.kwargs.get("files")

        upload_dir = Environment.get_upload_dir(ticket)
        for i, path in enumerate(files):

            path = path.replace("\\", "/")
            basename = os.path.basename(path)
            #basename = File.get_filesystem_name(basename) #changed File to Common in download from 4/15 
            basename = Common.get_filesystem_name(basename) 
            new_path = "%s/%s" % (upload_dir, basename)
            context = "publish"

            file_paths = [new_path]
            source_paths = [new_path]
            file_types = ['main']
            # if this is a file, then try to create an icon
            if os.path.isfile(new_path):
                icon_creator = IconCreator(new_path)
                icon_creator.execute()

                web_path = icon_creator.get_web_path()
                icon_path = icon_creator.get_icon_path()
                if web_path:
                    file_paths = [new_path, web_path, icon_path]
                    file_types = ['main', 'web', 'icon']
                    source_paths.append(web_path)
                    source_paths.append(icon_path)

            # specify strict checkin_type to prevent latest versionless generated
            checkin = FileCheckin(note, file_paths= file_paths, file_types = file_types, \
                    source_paths=source_paths,  context=context, checkin_type='strict')

            checkin.execute()



class NoteStatusEditWdg(BaseRefreshWdg):
    ''' Custom widget used in the prompt for changing note status'''

    def get_display(my):
        values_map = ProdSetting.get_map_by_key('note_status')
        if not values_map:
            # put in a default
            ProdSetting.create('note_status', 'new:N|read:R|old:O|:', 'map',\
                description='Note Statuses', search_type='sthpw/note')

        labels = []
        values = []
        for key, value in values_map:
            desc = key
            if desc == '':
                desc = '&lt; empty &gt;'
            labels.append('%s'%(desc))
            values.append(key)

        div = DivWdg(css='note_edit_top')
        select = SelectWdg('note_status')
        select.set_option('empty','true')
        select.set_option('values', values)
        select.set_option('labels', labels)
        div.add(select)

        sk = my.kwargs.get('search_key')
        note = SearchKey.get_by_search_key(sk)
        if note:
            current_status = note.get_value('status')
            select.set_value(current_status)

        return div

