#!/usr/bin/env python

import ply.yacc as yacc

from token_out import tokens, tokenize

class AST(object):
  def __init__(self):
    self.children = []
    self.walk_results = []

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

def p_text_affect(p):
  'text : text affect'
  p[0] = p[1].add_child(p[2])

def p_text_ability(p):
  'text : text ability'
  p[0] = unimplemented()

def p_text_cost(p):
  'text : cost'
  p[0] = p[1]

def p_text_none(p):
  'text : '
  p[0] = text()

def p_ability_static(p):
  'ability : affect time'
  p[0] = unimplemented()

def p_ability_triggered(p):
  'ability : trigger COMMA affect'
  p[0] = unimplemented()

def p_time_untap(p):
  'time : DURING YOUR UNTAP STEP'
  p[0] = unimplemented()

def p_trigger_etb(p):
  'trigger : WHENEVER object ENTERS THE BATTLEFIELD'
  p[0] = unimplemented()

def p_doesnt(p):
  'doesnt : DOESN APOSTROPHE T'
  p[0] = None

def p_affect_stay_tapped(p):
  'affect : TILDE doesnt UNTAP'
  p[0] = unimplemented()

def p_affect_damage(p):
  'affect : TILDE DEALS number DAMAGE TO object'
  p[0] = damage_affect(p[3], p[6])

def p_object_backreference_controller(p):
  'object : backref APOSTROPHE S CONTROLLER'
  p[0] = unimplemented()

def p_object_a(p):
  'object : A type'
  p[0] = unimplemented()

def p_object_target(p):
  'object : TARGET type'
  p[0] = target(p[2])

def p_backref(p):
  'backref : THAT type'
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

def p_type_land(p):
  'type : LAND'
  p[0] = p[1]

def p_number_num(p):
  'number : NUM'
  p[0] = int(p[1])

def p_cost_number(p):
  'cost : number'
  p[0] = cost().add_child(p[1])

def p_cost_color(p):
  'cost : cost color'
  p[0] = p[1].add_child(p[2])

def p_cost_term(p):
  'cost : color'
  p[0] = cost().add_child(p[1])

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

parser = yacc.yacc()

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
        import pdb;pdb.set_trace()
        raise
