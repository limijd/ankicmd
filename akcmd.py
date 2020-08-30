#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import logging
from texttable import Texttable
from argparse import ArgumentParser
from anki.collection import Collection
from akbuilder import *

SCRIPT = os.path.basename(__file__)

def do_collection_list_deck(bcol:BCollection, args):
    table = [["Deck ID", "Deck Name", "Cards", "Notes", "noteTypes", "cardTypes"]]
    for k, bd in sorted(bcol.bdecks.items()):
        table.append([bd.id, bd.name, 0, 0, len(bd.noteTypes), len(bd.cardTypes)])
    tt = Texttable()
    tt.set_cols_dtype(['i', 't', 'i', 'i', 'i', 'i'])
    tt.add_rows(table)
    print(tt.draw())
    print("Total: Decks: %d, Notes: %d, Cards: %d, NoteTypes: %d, CardTypes: %d" \
          % (len(bcol.bdecks), bcol.col.noteCount(), bcol.col.cardCount(), len(bcol.bnoteTypes), len(bcol.bcardTypes)))
    return

def do_collection_list_note_types(bcol, args):
    tt = Texttable()
    tt.set_cols_dtype(['i', 't', 't', 't'])
    table = []
    table.append(["NoteType ID", "NoteType Name", "CardTypes", "Fields"])
    for ntid, bnt in sorted(bcol.bnoteTypes.items()):
        bcts = bnt.bcardTypes.values()
        bfds = bnt.bfields.values()
        fdnames = map(lambda x:x.name, bfds)
        ctnames = map(lambda x:x.name, bcts)
        table.append([bnt.id, bnt.name, ",".join(ctnames), ",".join(fdnames)])
    tt.add_rows(table)
    print(tt.draw())
    return

def do_collection(args):
    print(args.anki_db)
    if not os.path.exists(args.anki_db):
        logging.error("ANKI database doesn't exist: %s" % args.anki_db)
        sys.exit(-1)
    try:
        col = Collection(args.anki_db)
    except Exception as e:
        logging.error("ANKI database loading error: %s" % e)
        sys.exit(-2)

    logging.debug("%s loaded successfully." % args.anki_db)

    logging.debug("Building class objects from database...")
    bcol = BCollection(col)
    bcol.build()

    if args.list_deck:
        do_collection_list_deck(bcol, args)

    if args.list_note_types:
        do_collection_list_note_types(bcol, args)

    return

def main():
    parser: ArgumentParser = argparse.ArgumentParser(prog=SCRIPT, description="ANKI command line tool")
    parser.add_argument('-d', '--debug', action='store_true', help="debug mode")
    sub_parsers = parser.add_subparsers(help='sub commands supported')

    parser_collection = sub_parsers.add_parser("collection", help='command operates collection')
    parser_collection.add_argument("anki_db", help='ANKI collection database, typically it\'s collection.ank2')
    parser_collection.add_argument('-ld', '--list_deck', action='store_true', help="list decks")
    parser_collection.add_argument('-lnt', '--list_note_types', action='store_true', help="list note types")
    parser_collection.set_defaults(func=do_collection)

    parser_deck = sub_parsers.add_parser('deck', help='command operates deck')
    parser_card = sub_parsers.add_parser('card', help='command operates card')
    parser_note = sub_parsers.add_parser('note', help='command operates note')
    parser_tag = sub_parsers.add_parser('tag', help='command operates tag')

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
    return

if __name__ == "__main__":
    main()

