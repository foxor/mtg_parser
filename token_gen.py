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

number = r"^(\d*)$"
re_number = re.compile(number)

replacements = {
  re.compile(r"Variable Colorless"): "x",
  re.compile(r"'"): " apostrophe ",
  re.compile(r":"): " colon ",
  re.compile(r"\+"): "plus ",
  re.compile(r"-"): " minus ",
  re.compile(r"\."): " period ",
  re.compile(r"/"): " slash ",
  re.compile(r"\["): " open_bracket ",
  re.compile(r"\]"): " close_bracket ",
  re.compile(r","): " comma ",
  re.compile(r"\("): " lparen ",
  re.compile(r"\)"): " rparen ",
}

allowed_punctuation = "+/[]-,:"

disallowed = r"[^a-zA-Z0-9\s~" + re.escape(allowed_punctuation) + r"]"


DEBUG = False
#DEBUG = True

def sanitize(card_name, card_text):
  # Name based substitutions take precidence
  card_text = re.sub(card_name, " tilde ", card_text)
  if "," in card_name:
    card_text = re.sub(card_name.split(',')[0], " tilde ", card_text)

  # Pull semantically significant punctuation into words that can be lexed by the same process as the rest of the card
  for regex, sub in replacements.iteritems():
    card_text = re.sub(regex, sub, card_text)
  card_text = re.sub(disallowed, "", card_text)
  return card_text.lower()

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
""" % (",".join("'%s'" % x.upper() for x in sorted_words + ["NUM"]), "\n".join("t_%s = r'%s'" % (x.upper(), x) for x in sorted_words), word_seperator)

if __name__ == '__main__':
  main()
