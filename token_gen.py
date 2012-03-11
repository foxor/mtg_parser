#!/usr/bin/env python

import MySQLdb
import re
import string

from password import password

_conn = MySQLdb.connect (host = "localhost", user = "root", passwd = password, db = "mtg").cursor()
def get_cards():
  _conn.execute("SELECT r.text, c.card_name FROM `rules_text` r, (SELECT multiverse_id, card_name from cards group by card_name) c WHERE c.multiverse_id = r.card and r.flavor = 0")
  r = _conn.fetchone()
  while r:
    yield r[0], r[1]
    r = _conn.fetchone()

word_seperator = r"[\[\]+-/ ]"
re_sep = re.compile(word_seperator)

variable_colorless = r"Variable Colorless"
re_variable = re.compile(variable_colorless)

number = r"^(\d*)$"
re_number = re.compile(number)

apostrophe = r"'"
re_apostrophe = re.compile(apostrophe)

colon = r':'
re_colon = re.compile(colon)

allowed_punctuation = "+/[]-,:"

disallowed = r"[^a-zA-Z0-9\s~" + re.escape(allowed_punctuation) + r"]"


DEBUG = False
#DEBUG = True

def sanitize(card_name, card_text):
  transformed_text = re.sub(re_variable, "x", card_text)
  transformed_text = re.sub(card_name, "~", transformed_text)
  transformed_text = re.sub(re_apostrophe, " apostrophe ", transformed_text)
  transformed_text = re.sub(re_colon, " colon ", transformed_text)
  if "," in card_name:
    transformed_text = re.sub(card_name.split(',')[0], "~", transformed_text)
  transformed_text = re.sub(disallowed, "", transformed_text)
  return transformed_text.lower()

def main():
  trans = string.maketrans("","")
  words = {}
  punc = string.punctuation.translate(trans, allowed_punctuation)
  filters = [re_number]
  for card_text, card_name in get_cards():
    transformed_text = sanitize(card_name, card_text)
    for word in re_sep.split(transformed_text.translate(trans, punc)):
      if any(x.match(word) for x in filters):
        #if DEBUG:
        #  print "IGNORING \t%s\t%s" % (word, card_name)
        continue
      if DEBUG:
        count, cards = words.get(word, (0, []))
        words[word] = (count + 1, cards + [card_name])
      else:
        words[word] = words.get(word, 0) + 1
  if DEBUG:
    sorted_words = [(k,v[1][:5]) for k,v in words.iteritems()]
    sorted_words.sort(key = lambda x: words[x[0]][0])
    sorted_words = [str(x) for x in sorted_words]
  else:
    sorted_words = words.keys()
    sorted_words.sort(key = lambda x: -words[x])
  print """#!/usr/bin/env python
import ply.lex as lex
from token_gen import sanitize

tokens = (%s)

%s

allowed_punctuation = "+/[]-,"
t_TILDE = r'~'
t_COMMA = r','
t_PLUS_SYMBOL = r'\+'
t_MINUS_SYMBOL = r'-'
t_SLASH = r'/'
t_OPEN_BRACKET = r'\['
t_CLOSE_BRACKET = r'\]'

def t_NUM(t):
  r'\d+'
  t.value = int(t.value)
  return t

t_ignore = r'%s'

lexer = lex.lex()

def tokenize(card_name, card_text):
  lexer.input(sanitize(card_name, card_text))
  return lexer

if __name__ == '__main__':
  for token in tokenize("Lightning Bolt", "Lightning Bolt deals 3 damage to target creature or player"):
    print token
""" % (",".join("'%s'" % x.upper() for x in sorted_words + ["NUM", "TILDE", "COMMA", "PLUS_SYMBOL", "MINUS_SYMBOL", "SLASH", "OPEN_BRACKET", "CLOSE_BRACKET"]), "\n".join("t_%s = r'%s'" % (x.upper(), x) for x in sorted_words), word_seperator)

if __name__ == '__main__':
  main()
