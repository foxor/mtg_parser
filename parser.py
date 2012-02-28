#!/usr/bin/env python

import ply.yacc as yacc

from token_out import tokens, tokenize

class AST(object):
  def __init__(self):
    self.children = []

  def walk(self, name, *args, **kwargs):
    if hasattr(self, name):
      getattr(self, name)(*args, **kwargs)
    for child in get_children():
      child.walk(name, *args, **kwargs)
    return self

  def add_child(self, child):
    self.children += [child]
    return self

  def get_children(self):
    return self.children

class Instant(AST):
  def __init__(self, text, cost, name):
    self.text = text
    self.cost = cost
    self.name = name

  def play(self, *args, **kwargs):
    self.walk("cast", *args, **kwargs)

  def pop(self, *args, **kwargs):
    self.walk("resolve", *args, **kwargs)

  def cast(self, *args, **kwargs):
    kwargs['player'].game.deduct_mana(self.cost)

  def get_children(self):
    return [text]

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

  def play(self, *args, **kwargs):
    kwargs['name'] = '%s:%s' % (kwargs['player'].name, self.name)
    kwargs['types'] = self.types
    kwargs['player'].game.move_to_battlefield(kwargs)

  def activate(self, *args, **kwargs):
    kwargs['player'].mana_pool.append({'mana': self.color})

class ability(AST):
  pass

class text(AST):
  def __init__(self):
    self.abilities = []
  def add_affect(self, ability):
    self.abilities += [ability]
    return self

class affect(AST):
  pass

class damage_affect(affect):
  def __init__(self, number, target):
    self.number = number
    self.target = target

class player_choice(AST):
  def __init__(self, *args):
    self.choices = args

class cost(AST):
  pass

class color(AST):
  pass

class white(color):
  pass

class red(color):
  pass

class green(color):
  pass

class blue(color):
  pass

class black(color):
  pass

def p_text_affect(p):
  'text : text affect'
  p[0] = p[1].add_affect(p[2])

def p_text_cost(p):
  'text : cost'
  p[0] = p[1]

def p_text_none(p):
  'text : '
  p[0] = text()

def p_affect_damage(p):
  'affect : TILDE DEALS number DAMAGE TO object'
  p[0] = damage_affect(p[3], p[6])

def p_object_target(p):
  'object : TARGET type'
  p[0] = p[2]

def p_type_choice(p):
  'type : type OR type'
  p[0] = player_choice(p[1], p[3])

def p_type_creature(p):
  'type : CREATURE'
  p[0] = p[1]

def p_type_player(p):
  'type : PLAYER'
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
  print parse("Lightning Bolt", "Lightning Bolt deals 3 damage to target creature or player")
