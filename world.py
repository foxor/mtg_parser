#!/usr/bin/env python

import itertools
import uuid
import json
import MySQLdb
import random

from parser import parse, Instant, Sorcery, Creature, Artifact, Enchantment, Land, BasicLand
from password import password

_conn = MySQLdb.connect (host = "localhost", user = "root", passwd = password, db = "mtg").cursor()
def get_card_by_name(name):
  _conn.execute("SELECT * FROM `cards` WHERE card_name = '%s'" % name)
  return _conn.fetchone()

def get_rules_per_card(card):
  _conn.execute("SELECT * FROM `rules_text` where `card` = %d" % card[0])
  return _conn.fetchall()

def get_types_per_card(card):
  _conn.execute("SELECT * FROM `types` where `card` = %d" % card[0])
  return _conn.fetchall()

def interpert(name, text, types, card):
  if 'Basic' in types and 'Land' in types:
    return BasicLand(name, text, types)
  ast_text = parse(name.lower(), text.lower())
  ast_cost = parse(name.lower(), card[2].lower())
  print "="*80
  print "CARD INFO"
  print ast_cost
  print ast_text
  print "="*80
  if 'Instant' in types:
    return Instant(ast_text, ast_cost, name)
  raise Exception("Not Implemented")

_card_code = {}
def card_code(name):
  if not name in _card_code:
    card = get_card_by_name(name)
    rules = get_rules_per_card(card)
    types = get_types_per_card(card)
    code = interpert(name, ' '.join([x[2] for x in rules]), [x[1] for x in types], card)
    _card_code[name] = code
  return _card_code[name]

class card_pile(object):
  def __init__(self, cards=None):
    self.cards = cards if cards else []
    self.sub_piles = []
    self.visible_to = []

  def partition(self, partition_lengths):
    pass

  def shuffle(self):
    self.cards.sort(key=lambda x:random.randint(0,20))
    self.cards.sort(key=lambda x:random.randint(0,20))
    self.cards.sort(key=lambda x:random.randint(0,20))
    self.cards.sort(key=lambda x:random.randint(0,20))

  def shuffle_into(self, other):
    while self.cards:
      other.add_card(self.pop_card())
    other.shuffle()

  def add_card(self, card):
    self.cards.append(card)

  def pop_card(self):
    return self.cards.pop()

  def remove_card(self, card_name):
    found = False
    i = 0
    for i in xrange(len(self.cards)):
      #TODO: ORM this
      if self.cards[i][1].lower().startswith(card_name.lower()):
        found = True
        break
    if found:
      return self.cards.pop(i)

  def __repr__(self):
    #TODO: ORM this
    return [x[1] for x in self.cards].__repr__()
    #return [x.name for x in self.cards].__repr__()

class player(object):
  '''These are metagame players.  They might have rankings attached to them, or decks attributed to them, or participate in games or be saved in a database'''
  
  def __getitem__(self, item):
    #we want to acces this like a dict, so it looks like a normal card
    return getattr(self, item)

  def start_game(self, game):
    self.mill_loss = None
    self.game = game
    self.hand = card_pile()
    self.library = card_pile()
    self.graveyard = card_pile()
    self.battle_field = {}
    self.exile = card_pile()
    self.mana_pool = []
    self.choose_deck()
    self.life = 20
    self.prep_pregame_roll()
    self.library.shuffle()
    self.draw_hand()
    self.name = random.choice(['timmy', 'jonny', 'spike'])

  def play(self, card_name, *args, **kwargs):
    kwargs['player'] = self
    kwargs['card'] = self.hand.remove_card(card_name)
    if not kwargs['card']:
      print "No such card in your hand"
    else:
      card_code(card_name).play(*args, **kwargs)

  def activate(self, card_name, *args, **kwargs):
    card_code(card_name).play(self, *args, **kwargs)

  def choose_deck(self):
    for i in range(43):
      self.library.add_card(get_card_by_name("Lightning Bolt"))
    for i in range(17):
      self.library.add_card(get_card_by_name("Mountain"))

  def prep_pregame_roll(self):
    self.pregame_roll = random.randint(0,20)

  def apply_damage(self, number):
    self.life -= number

  def choose(self, choices):
    print "="*80
    print "Choosing between: "
    print choices
    print "="*80
    return list(choices)[-1]

  def approve_hand(self):
    print "Looking at a %s, keep?" % self.hand
    print "Keeping"
    return True

  def deduct_mana(self, cost):
    backup_pool = self.mana_pool
    for mana in cost:
      if mana in self.mana_pool:
        self.mana_pool = self.mana_pool[:self.mana_pool.index(mana)] + self.mana_pool[self.mana_pool.index(mana) + 1:]
      else:
        self.mana_pool = backup_pool
        return False
    return True

  def get_hand(self):
    return self.hand

  def draw_hand(self):
    for mulligan in range(7):
      self.hand.shuffle_into(self.library)
      for card in range(7-mulligan):
        self.draw_card()
      if (self.approve_hand()):
        break
      self.hand.shuffle_into(self.library)

  def draw_card(self):
    if not self.library:
      self.mill_loss = True
    else:
      card = self.library.pop_card()
      self.hand.add_card(card)
      return card

  def pregame_opportunity(self):
    pass

  def __repr__(self):
    return "%s:%s" % (self.name, self.life)

class step(object):
  @staticmethod
  def phasing(game):
    pass
  @staticmethod
  def untap(game):
    pass
  @staticmethod
  def begin_turn_trigger(game):
    pass
  @staticmethod
  def priority(game):
    pass
  @staticmethod
  def draw(game):
    print "Drawing a %s, current hand is %s" % (game.get_active_player().draw_card(), game.get_active_player().get_hand())
  @staticmethod
  def draw_trigger(game):
    pass
  @staticmethod
  def priority(game):
    game.check_status()
    pass
  @staticmethod
  def clear_mana_pool(game):
    pass
  @staticmethod
  def begin_main_trigger(game):
    pass
  @staticmethod
  def empty_stack(my_game):
    done = None
    while not done:
      print "MOCK MENU"
      print "Your hand: %s" % my_game.get_active_player().hand
      print "Valid targets: %s" % game.repr_types_dict(**my_game.targets)
      print "Your battlefield: %s" % game.repr_types_dict(**my_game.get_active_player().battle_field)
      print "Your mana pool: %s" % my_game.get_active_player().mana_pool
      print "Do you wish to do anything?"
      choice = raw_input().split(':')
      if not choice[0]:
        choice = "play Lightning Bolt".split(':')
      parsed = [choice[0].split(' ')[0], ' '.join(choice[0].split(' ')[1:])]
      args = (choice[1].split(' ') if len(choice) > 1 and choice[1] else [])
      kwargs = json.loads(':'.join(choice[2:]).strip() if len(choice) > 2 else '{}')
      print parsed, args, kwargs
      if choice[0] == "done":
        break
      elif parsed[0] == "play" and len(parsed) == 2:
        my_game.play(parsed[1], *args, **kwargs)
      elif parsed[0] == "activate" and len(parsed) == 2:
        my_game.activate(parsed[1], *args, **kwargs)
    print "Done"
  @staticmethod
  def begin_combat_trigger(game):
    pass
  @staticmethod
  def declare_attackers(game):
    pass
  @staticmethod
  def declare_attackers_trigger(game):
    pass
  @staticmethod
  def declare_blockers(game):
    pass
  @staticmethod
  def declare_blockers_trigger(game):
    pass
  @staticmethod
  def declare_first_strike_attack_damage(game):
    pass
  @staticmethod
  def declare_first_strike_block_damage(game):
    pass
  @staticmethod
  def first_strike_combat_damage(game):
    pass
  @staticmethod
  def combat_damage_trigger(game):
    pass
  @staticmethod
  def declare_attack_damage(game):
    pass
  @staticmethod
  def declare_block_damage(game):
    pass
  @staticmethod
  def combat_damage(game):
    pass
  @staticmethod
  def until_end_combat_trigger(game):
    pass
  @staticmethod
  def end_combat_trigger(game):
    pass
  @staticmethod
  def end_turn_trigger(game):
    pass
  @staticmethod
  def discard(game):
    pass
  @staticmethod
  def until_end_turn_trigger(game):
    pass
  @staticmethod
  def check_state(game):
    pass
  @staticmethod
  def stack_triggers(game):
    pass
  @staticmethod
  def cleanup_loop(game):
    pass

class phase(object):
  def __init__(self):
    self.steps = []
  def has_step(self):
    return bool(self.steps)
  def add_step(self, step):
    self.steps.reverse()
    self.steps.append(step)
    self.steps.reverse()
  def pop_step(self):
    return self.steps.pop()

class begin_phase(phase):
  def __init__(p):
    super(begin_phase, p).__init__()
    p.add_step(step.phasing)
    p.add_step(step.untap)
    p.add_step(step.begin_turn_trigger)
    p.add_step(step.priority)
    p.add_step(step.draw)
    p.add_step(step.draw_trigger)
    p.add_step(step.priority)
    p.add_step(step.clear_mana_pool)

class main_phase(phase):
  def __init__(p):
    super(main_phase, p).__init__()
    p.add_step(step.begin_main_trigger)
    p.add_step(step.priority)
    p.add_step(step.empty_stack)
    p.add_step(step.clear_mana_pool)

class combat_phase(phase):
  def __init__(p):
    super(combat_phase, p).__init__()
    p.add_step(step.begin_combat_trigger)
    p.add_step(step.priority)
    p.add_step(step.declare_attackers)
    p.add_step(step.declare_attackers_trigger)
    p.add_step(step.priority)
    p.add_step(step.declare_blockers)
    p.add_step(step.declare_blockers_trigger)
    p.add_step(step.priority)
    p.add_step(step.declare_first_strike_attack_damage)
    p.add_step(step.declare_first_strike_block_damage)
    p.add_step(step.first_strike_combat_damage)
    p.add_step(step.combat_damage_trigger)
    p.add_step(step.priority)
    p.add_step(step.declare_attack_damage)
    p.add_step(step.declare_block_damage)
    p.add_step(step.combat_damage)
    p.add_step(step.combat_damage_trigger)
    p.add_step(step.priority)
    p.add_step(step.until_end_combat_trigger)
    p.add_step(step.end_combat_trigger)
    p.add_step(step.priority)
    p.add_step(step.clear_mana_pool)

class end_phase(phase):
  def __init__(p):
    super(end_phase, p).__init__()
    p.add_step(step.end_turn_trigger)
    p.add_step(step.priority)
    p.add_step(step.discard)
    p.add_step(step.until_end_turn_trigger)
    p.add_step(step.check_state)
    p.add_step(step.stack_triggers)
    p.add_step(step.cleanup_loop)
    p.add_step(step.clear_mana_pool)

class turn(object):
  def __init__(self, player):
    self.phases = [
      begin_phase(),
      main_phase(),
      combat_phase(),
      main_phase(),
      end_phase()
    ]
    self.player = player
  def has_phase(self):
    return bool(self.phases)
  def pop_phase(self):
    return self.phases.pop()

class game(object):
  def __init__(self, players):
    self.players = players
    self.active_player = 0
    self.triggers = []
    self.stack = []
    self.phases = []
    self.targets = {'player': [x for x in players]}
    self.turn_stage = 0
    self.status_message = "Starting The Game"
    for player in self.players:
      player.start_game(self) #TODO: parallelize this, since each player is independant
    self.order_players()
    for player in self.get_players():
      player.pregame_opportunity()
    self.turn_loop()

  @staticmethod
  def repr_types_dict(**kwargs):
    return set(sum([[x.__repr__() for x in kwargs[y]] for y in kwargs], []))

  def push_stack(self, spell):
    self.stack.append(spell)
    self.pop_stack()

  def pop_stack(self):
    # Call the "pop" method of the top spell on the stack and remove it
    self.stack.pop().pop()

  def get_targets_of_type(self, target_type):
    return self.targets[target_type]

  def order_players(self):
    players.sort(key=lambda x: x.pregame_roll)

  def get_players(self, start_player=None):
    start_player = start_player or self.active_player
    yield self.players[start_player]
    cur_player = start_player + 1
    while cur_player % len(self.players) != start_player:
      yield self.players[cur_player % len(self.players)]
      cur_player += 1

  def move_to_battlefield(self, card):
    for card_type in card.types:
      self.targets[card_type] = self.targets.get(card_type, []) + [card]
      card.player.battle_field[card_type] = card.player.battle_field.get(card_type, []) + [card]

  def play(self, card_name, *args, **kwargs):
    self.get_active_player().play(card_name, *args, **kwargs)

  def activate(self, card_name, *args, **kwargs):
    match = set(itertools.chain(*[[y for y in self.get_active_player().battle_field[x] if y.name == card_name] for x in self.get_active_player().battle_field]))
    self.get_active_player().choose(match).activate(*args, **kwargs)

  def get_active_player(self):
    return self.players[self.active_player]

  def stack_triggers(self, opportunity):
    pass

  def check_status(self):
    pass

  def game_over(self):
    return False

  def turn_loop(self):
    #import pdb;pdb.set_trace()
    while not self.game_over():
      active_turn = turn(self.get_active_player())
      while active_turn.has_phase():
        active_phase = active_turn.pop_phase()
        while active_phase.has_step():
          active_phase.pop_step()(self)



players = [player(), player()]
mtg_game = game(players)
