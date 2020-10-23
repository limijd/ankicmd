#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=C0103,W0703

"""
ANKI command line tools
"""

import os
import sys
import argparse
import logging
from argparse import ArgumentParser
from texttable import Texttable
from anki.collection import Collection
from akbuilder import BCollection
from anki.importing import TextImporter

def do_list_deck(bcol:BCollection):
    '''--list_deck '''
    table = [["Deck ID", "Deck Name", "Cards", "Notes", "noteTypes", "cardTypes"]]
    for dummy, bdeck in sorted(bcol.bdecks.items()):
        table.append([bdeck.id, bdeck.name, 0, 0, len(bdeck.noteTypes), len(bdeck.cardTypes)])
    text_table = Texttable()
    text_table.set_cols_dtype(['i', 't', 'i', 'i', 'i', 'i'])
    text_table.add_rows(table)
    print(text_table.draw())
    print("Total: Decks: %d, Notes: %d, Cards: %d, NoteTypes: %d, CardTypes: %d" \
          % (len(bcol.bdecks), bcol.col.noteCount(), bcol.col.cardCount(),
             len(bcol.bnoteTypes), len(bcol.bcardTypes)))

def do_list_note_types(bcol):
    '''--list_note_types '''
    text_table = Texttable()
    text_table.set_cols_dtype(['i', 't', 't', 't'])
    table = []
    table.append(["NoteType ID", "NoteType Name", "CardTypes", "Fields"])
    for dummy, bnt in sorted(bcol.bnoteTypes.items()):
        bcts = bnt.bcardTypes.values()
        bfds = bnt.bfields.values()
        fdnames = map(lambda x:x.name, bfds)
        ctnames = map(lambda x:x.name, bcts)
        table.append([bnt.id, bnt.name, ",".join(ctnames), ",".join(fdnames)])
    text_table.add_rows(table)
    print(text_table.draw())

def do_export_deck_note(bcol, deck_name, key_only):
    '''--export_deck_note'''
    export_bdeck = None
    for dummy, bdeck in sorted(bcol.bdecks.items()):
        if deck_name == bdeck.name:
            export_bdeck = bdeck

    if not export_bdeck:
        logging.error("Deck: %s not found.", deck_name)

    notes = export_bdeck.queryNotes()
    keys = map(lambda x:x[0], notes)
    for k in keys:
        print(k)
    return

def do_import_notes(bcol, deck_name, data_file, note_type, delimiter="\t"):
    col = bcol.col

    existingNotes = {}

    #load existing notes
    bdeck = None
    for dummy, bdk in sorted(bcol.bdecks.items()):
        if deck_name == bdk.name:
            bdeck = bdk
    assert bdeck
    notes = bdeck.queryNotes()
    for n in notes:
        note_id, note_subject, note_content, note_tags = n
        note_content=note_content.split("\x1f")[1]
        note_tags = note_tags.strip()
        existingNotes[note_subject] = [note_id, note_subject, note_content, note_tags]

    nochangeNotes = {}
    toBeImportNotes = {}
    toBeUpdatedNotes = {}
    #load data fiel
    fp = open(data_file, "r")
    for line in fp.readlines():
        line = line.strip()
        parts = line.split("\t")
        subject = parts[0]
        content = parts[1]
        if len(content)>int(131072*0.8): #131072 is limit of ANKI field
            logging.error("Content too long to import: %d, note: %s", len(content), subject)
            sys.exit(1)
        if len(parts)==3:
            tags = parts[2]
            tags = tags.strip()
        else:
            tags = ""
        if subject in existingNotes:
            #compare content and tags
            exist_note = existingNotes[subject]
            if content == exist_note[2] and tags == exist_note[3]:
                #doesn't need to be updated
                nochangeNotes[subject] = True
                pass
            else:
                logging.info("Updated note: %s", subject)
                toBeUpdatedNotes[subject] = [subject ,content, tags, exist_note[0]]
        else:
            logging.info("New note: %s", subject)
            toBeImportNotes[subject] = [subject, content, tags]
    fp.close()

    logging.info("%d notes wll be kept without any change", len(nochangeNotes))
    logging.info("%d notes need to be updated.", len(toBeUpdatedNotes))
    logging.info("%d notes need to be added.", len(toBeImportNotes))

    if not toBeUpdatedNotes and not toBeImportNotes:
        col.close()
        logging.info("No new note need to be imported! Bye!")
        sys.exit(1)

    #set current model
    deck_id = col.decks.id(deck_name)
    model = col.models.byName(note_type)
    if deck_id != model["did"]:
        model['did'] = deck_id
        col.models.save(model)

    col.models.setCurrent(model)

    logging.info("directly import: %s", data_file)
    ti = TextImporter(col, data_file)
    ti.allowHTML = True
    ti.needDelimiter = True
    ti.delimiter = "\t"
    ti.importMode = 0 #UPDATE_MODE
    ti.initMapping()
    ti.run()

    col.save()
    col.close()

    return

def do_cui(args):
    ''' CUI entry '''
    args.import_data_file = os.path.abspath(args.import_data_file)
    print(args.anki_db)
    if not os.path.exists(args.anki_db):
        logging.error("ANKI database doesn't exist: %s", args.anki_db)
        sys.exit(-1)
    try:
        col = Collection(args.anki_db)
    except Exception as e:
        logging.error("ANKI database loading error: %s" , e)
        sys.exit(-2)

    logging.debug("%s loaded successfully.", args.anki_db)

    logging.debug("Building class objects from database...")
    bcol = BCollection(col)
    bcol.build()

    if args.list_deck:
        do_list_deck(bcol)

    if args.list_note_types:
        do_list_note_types(bcol)

    if args.export_deck_note:
        deck_name = args.export_deck_note
        do_export_deck_note(bcol, deck_name, args.export_deck_note_only_key)

    if args.import_to_deck:
        deck_name = args.import_to_deck
        data_file = args.import_data_file
        note_type = args.import_note_type
        do_import_notes(bcol, deck_name, data_file, note_type, delimiter="\t")

def main():
    ''' main entry '''
    parser: ArgumentParser = argparse.ArgumentParser(prog=os.path.basename(__file__)
                                                     , description="ANKI command line tool")
    parser.add_argument("anki_db",
            help='ANKI collection database, typically it\'s collection.ank2')
    parser.add_argument('-d', '--debug', action='store_true', help="debug mode")
    parser.add_argument('-ld', '--list_deck', action='store_true', help="list decks")
    parser.add_argument('-lnt', '--list_note_types', action='store_true', help="list note types")
    parser.add_argument('-edn', '--export_deck_note', help="-edn <deckName> export the specified deck note")
    parser.add_argument('-ednok', '--export_deck_note_only_key', action='store_true', help="only export key column")
    parser.add_argument('-edc', '--export_deck_card', help="-edc=<deckName> export the specified deck card")
    parser.add_argument("-itd", "--import_to_deck", help="deck that the notes will be imported to ")
    parser.add_argument("-idf", "--import_data_file", help="text data file that contains records")
    parser.add_argument("-int", "--import_note_type", help="notetype to be used when do import")

    parser.set_defaults(func=do_cui)

    args = parser.parse_args()
    try:
        args.func
    except AttributeError:
        parser.error("too few arguments")

    if args.debug:
        logging.basicConfig(format='[AKCMD: %(asctime)s %(levelname)s] %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG)
    else:
        logging.basicConfig(format='[AKCMD: %(asctime)s %(levelname)s] %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)
    args.func(args)

if __name__ == "__main__":
    main()
