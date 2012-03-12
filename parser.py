#!/usr/bin/env python

import inspect
import ply.yacc as yacc

from token_out import tokens, tokenize

DEBUG = False

class AST(object):
  def __init__(self):
    self.children = []
    self.walk_results = []
    if DEBUG:
      stack = inspect.stack()
      for frame in range(1, len(stack)):
        if stack[frame][3] in globals() and ':' in globals()[stack[frame][3]].__doc__:
          print globals()[stack[frame][3]].__doc__
          break

  def walk(self, name, *args, **kwargs):
    if hasattr(self, "pre" + name):
      getattr(self, "pre" + name)(*args, **kwargs)
    for n, child in enumerate(self.get_children()):
      self.walk_results[n] = child.walk(name, *args, **kwargs)
    if hasattr(self, name):
      return getattr(self, name)(*args, **kwargs)
    return self.walk_results or self

  def add_child(self, child):
    self.children += [child]
    self.walk_results += [None]
    return self

  def get_children(self):
    return self.children

  def get_name(self):
    return "%s" % self.__class__

  def prerepresent(self, *args, **kwargs):
    kwargs['repr_args']['repr'] = kwargs['repr_args'].get('repr', []) + [(' ' * kwargs['repr_args'].get('indent', 0)) + self.get_name()]
    kwargs['repr_args']['indent'] = kwargs['repr_args'].get('indent', 0) + 1

  def represent(self, *args, **kwargs):
    kwargs['repr_args']['indent'] = kwargs['repr_args'].get('indent', 0) - 1

  def __repr__(self):
    repr_args = {
      'repr': [],
      'indent': 0
    }
    self.walk('represent', repr_args=repr_args)
    return '\n'.join(repr_args['repr'])

class spell(AST):
  def __init__(self, text, cost, name):
    super(spell, self).__init__()
    self.text = text
    self.cost = cost
    self.name = name
    self.add_child(text)

  def play(self, *args, **kwargs):
    self.walk("cast", *args, **kwargs)

  def pop(self, *args, **kwargs):
    self.walk("resolve", *args, **kwargs)

  def cast(self, *args, **kwargs):
    cost = self.cost.walk('mana', *args, **kwargs)
    if kwargs['player'].deduct_mana(cost):
      kwargs['player'].game.push_stack(self)
    else:
      print "Not enough mana"

class Instant(spell):
  def resolve(self, *args, **kwargs):
    self.walk("apply", *args, **kwargs)

class Sorcery(AST):
  pass

class Creature(AST):
  pass

class Artifact(AST):
  pass

class Enchantment(AST):
  pass

class Land(AST):
  pass

class BasicLand(AST):
  def __init__(self, name, color, types):
    self.name = name
    self.color = color
    self.types = types
    self.tapped = False
    super(BasicLand, self).__init__()

  def play(self, *args, **kwargs):
    self.player = kwargs['player']
    if self.player.game.choose_land_effect():
      self.player.game.move_to_battlefield(self)

  def activate(self, *args, **kwargs):
    if not self.tapped:
      self.player.mana_pool.append(self.color)
      self.tapped = True
    else:
      print "Already Tapped"

class unimplemented(AST):
  def walk(*args, **kwargs):
    raise Exception("Not Implemented")

class ability(AST):
  pass

class text(AST):
  def __init__(self):
    super(text, self).__init__()

class affect(AST):
  pass

class damage_affect(affect):
  def __init__(self, number, target):
    self.number = number
    super(damage_affect, self).__init__()
    self.add_child(target)

  def get_name(self):
    return "%s damage to" % self.number

  def apply(self):
    return self.walk_results[0].apply_damage(self.number)

class target(AST):
  def __init__(self, child):
    super(target, self).__init__()
    self.add_child(child)

  def get_name(self):
    return "target"

  def apply(self, *args, **kwargs):
    return self.cast_target

  def cast(self, *args, **kwargs):
    self.cast_target = kwargs['player'].choose(kwargs['player'].game.get_targets_of_type(self.walk("targeting", *args, **kwargs)))
    return self.cast_target
    
  def targeting(self, *args, **kwargs):
    return self.walk_results[0]

class player_choice(AST):
  def __init__(self, *args):
    self.choices = args
    super(player_choice, self).__init__()

  def get_name(self):
    return ", ".join(self.choices) or ""

  def targeting(self, *args, **kwargs):
    return kwargs['player'].choose(self.choices)

class cost(AST):
  pass

class color(AST):
  pass

class white(color):
  def mana(*args, **kwargs):
    return "W"

class red(color):
  def mana(*args, **kwargs):
    return "R"

class green(color):
  def mana(*args, **kwargs):
    return "G"

class blue(color):
  def mana(*args, **kwargs):
    return "U"

class black(color):
  def mana(*args, **kwargs):
    return "B"

def p_error(p):
  raise Exception("No Errors allowed: %s" % p)

start = "text"

def p_text_term(p):
  'text : text_part'
  p[0] = p[1]

def p_text_recur(p):
  'text : text text_part'
  p[0] = p[1].add_child(p[2])

def p_text_affect(p):
  'text_part : affect'
  p[0] = p[1]

def p_text_ability(p):
  'text_part : ability'
  p[0] = unimplemented()

def p_text_cost(p):
  'text_part : cost'
  p[0] = p[1]

def p_ability_static(p):
  'ability : affect time'
  p[0] = unimplemented()

def p_ability_triggered(p):
  'ability : trigger COMMA affect'
  p[0] = unimplemented()

def p_ability_activated(p):
  'ability : cost COLON affect'

def p_time_upkeep(p):
  'time : AT THE BEGINNING OF object UPKEEP'
  p[0] = unimplemented()

def p_time_untap(p):
  'time : DURING YOUR UNTAP STEP'
  p[0] = unimplemented()

def p_etb(p):
  'etb : ENTERS THE BATTLEFIELD'
  p[0] = None

def p_trigger_time(p):
  'trigger : time'
  p[0] = unimplemented()

def p_trigger_etb_choice(p):
  'trigger : AS object etb'
  p[0] = unimplemented()

def p_trigger_etb(p):
  'trigger : WHENEVER object etb'
  p[0] = unimplemented()

def p_doesnt(p):
  'doesnt : DOESN APOSTROPHE T'
  p[0] = None

def p_affect_memory(p):
  'affect : CHOOSE object'
  p[0] = unimplemented()

def p_affect_stay_tapped(p):
  'affect : object doesnt UNTAP'
  p[0] = unimplemented()

def p_affect_untap(p):
  'affect : UNTAP object'
  p[0] = unimplemented()

def p_affect_where(p):
  'affect : affect COMMA where'
  p[0] = unimplemented()

def p_affect_damage(p):
  'affect : object DEALS number DAMAGE TO object'
  p[0] = damage_affect(p[3], p[6])

def p_affect_add_mana(p):
  'affect : ADD cost TO YOUR MANA POOL'
  p[0] = unimplemented()

def p_where(p):
  'where : WHERE X IS math_exp'
  p[0] = unimplemented()

def p_math_count(p):
  'math_exp : THE NUMBER OF count'
  p[0] = unimplemented()

def p_math_minus(p):
  'math_exp : math_exp MINUS math_exp'
  p[0] = unimplemented()

def p_math_const(p):
  'math_exp : number'
  p[0] = unimplemented()

def p_count_cards_hand(p):
  'count : CARDS IN object HAND'
  p[0] = unimplemented()

def p_a(p):
  'a : A'
  p[0] = None

def p_an(p):
  'a : AN'
  p[0] = None

def p_object_backreference(p):
  'object : backref'
  p[0] = unimplemented()

def p_object_backreference_possessive(p):
  'object : backref APOSTROPHE S'
  p[0] = unimplemented()

def p_object_backreference_controller(p):
  'object : backref APOSTROPHE S CONTROLLER'
  p[0] = unimplemented()

def p_object_a(p):
  "object : a type"
  p[0] = unimplemented()

def p_object_target(p):
  'object : TARGET type'
  p[0] = target(p[2])

def p_object_self(p):
  'object : TILDE'
  p[0] = unimplemented()

def p_backref_chosen_player(p):
  'backref : THE CHOSEN type'
  p[0] = unimplemented()

def p_backref_type(p):
  'backref : THAT type'
  p[0] = unimplemented()

def p_backref_gendered_player(p):
  'backref : HIS OR HER'
  p[0] = unimplemented()

def p_type_choice(p):
  'type : type OR type'
  p[0] = player_choice(p[1], p[3])

def p_type_creature(p):
  'type : CREATURE'
  p[0] = p[1]

def p_type_player(p):
  'type : PLAYER'
  p[0] = p[1]

def p_type_opponent(p):
  'type : OPPONENT'
  p[0] = p[1]

def p_type_land(p):
  'type : LAND'
  p[0] = p[1]

def p_number_num(p):
  'number : NUM'
  p[0] = int(p[1])

def p_number_x(p):
  'number : X'
  p[0] = unimplemented()

def p_number_one(p):
  'number : ONE'
  p[0] = 1

def p_number_two(p):
  'number : TWO'
  p[0] = 2

def p_number_three(p):
  'number : THREE'
  p[0] = 3

def p_number_four(p):
  'number : FOUR'
  p[0] = 4

def p_number_five(p):
  'number : FIVE'
  p[0] = 5

def p_number_six(p):
  'number : SIX'
  p[0] = 6

def p_number_seven(p):
  'number : SEVEN'
  p[0] = 7

def p_number_eight(p):
  'number : EIGHT'
  p[0] = 8

def p_number_nine(p):
  'number : NINE'
  p[0] = 9

def p_number_ten(p):
  'number : TEN'
  p[0] = 10

#def p_number_eleven(p):
#  'number : ELEVEN'
#  p[0] = 11

def p_number_twelve(p):
  'number : TWELVE'
  p[0] = 12

def p_number_thirteen(p):
  'number : THIRTEEN'
  p[0] = 13

#def p_number_fourteen(p):
#  'number : FOURTEEN'
#  p[0] = 14

def p_number_fifteen(p):
  'number : FIFTEEN'
  p[0] = 15

def p_cost_term(p):
  'cost : cost_part'
  p[0] = p[1]

def p_cost_recur(p):
  'cost : cost cost_part'
  p[0] = p[1].add_child(p[2])

def p_cost_cs(p):
  'cost : cost COMMA cost_part'
  p[0] = p[1].add_child(p[3])

def p_cost_choice(p):
  'cost_part : number MANA OF ANY COLOR'
  p[0] = unimplemented()

def p_cost_choice_mult(p):
  'cost_part : number MANA OF ANY ONE COLOR'
  p[0] = unimplemented()

def p_cost_sac(p):
  'cost_part : SACRIFICE object'
  p[0] = unimplemented()

def p_cost_part_tap(p):
  'cost_part : TAP'
  p[0] = unimplemented()

def p_cost_number(p):
  'cost_part : number'
  p[0] = cost().add_child(p[1])

def p_cost_color(p):
  'cost_part : color'
  p[0] = p[1]

def p_color_white(p):
  'color : WHITE'
  p[0] = white()

def p_color_red(p):
  'color : RED'
  p[0] = red()

def p_color_green(p):
  'color : GREEN'
  p[0] = green()

def p_color_blue(p):
  'color : BLUE'
  p[0] = blue

def p_color_black(p):
  'color : BLACK'
  p[0] = black

parser = yacc.yacc(debug=True)

def parse(card_name, card_text):
  return parser.parse(lexer=tokenize(card_name, card_text))

if __name__ == '__main__':
  import MySQLdb
  from password import password
  _conn = MySQLdb.connect (host = "localhost", user = "root", passwd = password, db = "mtg").cursor()
  _conn.execute("SELECT multiverse_id, card_name from `cards` LIMIT 10")
  for id, name in _conn.fetchall():
    _conn.execute("SELECT text from `rules_text` where `card` = %d and flavor = 0" % id)
    for card_text, in _conn.fetchall():
      try:
        parse(name, card_text)
        print ".",
      except Exception, e:
        print ""
        print name
        print '\n'.join(str(x) for x in tokenize(name, card_text))
        raise
