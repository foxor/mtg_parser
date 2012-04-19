#!/usr/bin/env python

import inspect
import ply.yacc as yacc

from token_out import tokens, tokenize

DEBUG = True

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

#def p_text_recur(p):
#  'text : text text_part'
#  p[0] = p[1].add_child(p[2])

def p_text_affect(p):
  'text_part : affect'
  p[0] = p[1]

def p_text_ability(p):
  'text_part : ability'
  p[0] = unimplemented()

def p_text_cost(p):
  'text_part : cost'
  p[0] = p[1]

def p_ability_recur(p):
  'ability : ability ability'
  p[0] = unimplemented()

def p_conjoined_ability(p):
  'ability : ability THEN ability'
  p[0] = unimplemented()

def p_ability_post_parenthetical(p):
  'ability : ability parenthetical PERIOD'
  p[0] = unimplemented()

def p_ability(p):
  'ability : ability_part PERIOD'
  p[0] = unimplemented()

def p_ability_parenthetical(p):
  'ability : ability_part parenthetical PERIOD'
  p[0] = unimplemented()

def p_ability_keyword_noperiod(p):
  'ability : keyword'
  p[0] = unimplemented()

def p_ability_keyword(p):
  'ability_part : keyword'
  p[0] = unimplemented()

def p_ability_triggered(p):
  'ability_part : trigger COMMA affect'
  p[0] = unimplemented()

def p_ability_triggered_nonstack(p):
  'ability_part : trigger WITH affect'
  p[0] = unimplemented()

def p_ability_triggered_initial_status(p):
  'ability_part : trigger affect'
  p[0] = unimplemented()

def p_ability_activated(p):
  'ability_part : cost COLON ability_part'
  p[0] = unimplemented()

def p_ability_affect(p):
  'ability_part : affect'
  p[0] = unimplemented()

def p_ability_activate_restriction(p):
  'ability_part : ACTIVATE THIS ABILITY ONLY time'
  p[0] = unimplemented()

def p_ability_event_impossible(p):
  'ability_part : object cant event'
  p[0] = unimplemented()

def p_ability_resolution_restriction(p):
  'ability_part : THIS ABILITY cant CAUSE status TO BE math_exp'
  p[0] = unimplemented()

def p_paren_word(p):
  '''paren_word : IN
                | ADDITION
                | TO
                | THE
                | MANA
                | LAND
                | ANY
                | CREATURES
                | WITH
                | BANDING
                | AND
                | UP
                | ONE
                | WITHOUT
                | COMMA
                | CAN
                | ATTACK
                | A
                | BAND
                | BANDS
                | ARE
                | BLOCKED
                | AS
                | GROUP
                | PERIOD
                | IF
                | PLAYER
                | CONTROLS
                | BLOCKING
                | BEING
                | CREATURE
                | THAT
                | DIVIDES
                | APOSTROPHE
                | S
                | COMBAT
                | OR
                | DAMAGE
                | NOT
                | IT
                | CONTROLLER
                | AMONG
                | OF
                | BY
                | ITS
                | IS
                | THIS
                | T
                | BE
                | EXCEPT
                | FLYING
                | REACH
                | DEALS
                | BEFORE
                | FIRST
                | STRIKE
                | TARGETED
                | DEALT
                | ENCHANTED
                | ANYTHING
                | color
                | UNBLOCKABLE
                | SWAMP
                | LONG
                | DEFENDING
                | PRODUCES'''
  p[0] = unimplemented()

def p_parenthisized(p):
  'parenthisized : paren_word parenthisized'
  p[0] = unimplemented()

def p_parenthisized_empty(p):
  'parenthisized :'
  p[0] = unimplemented()

def p_parenthetical(p):
  'parenthetical : LPAREN parenthisized RPAREN'
  p[0] = unimplemented()

def p_status_counter_count(p):
  'status : THE TOTAL NUMBER OF counter ON object'
  p[0] = unimplemented()

def p_damage_type_standard(p):
  'damage_type : DAMAGE'
  p[0] = unimplemented()

def p_damage_type_combat(p):
  'damage_type : COMBAT DAMAGE'
  p[0] = unimplemented()

def p_event_untap(p):
  'event : UNTAP math_exp object DURING time'
  p[0] = unimplemented()

def p_event_hypothetical(p):
  'event : object WOULD event'
  p[0] = unimplemented()

def p_event_unblocked(p):
  'event : DEAL damage_type TO object'
  p[0] = unimplemented()

def p_event_blocked(p):
  'event : BE BLOCKED'
  p[0] = unimplemented()

def p_event_conditional(p):
  'event : event conditional'
  p[0] = unimplemented()

def p_event_phase(p):
  'event : BEGIN YOUR phase'
  p[0] = unimplemented()

def p_phase_turn(p):
  'phase : TURN'
  p[0] = unimplemented()

def p_phase_combat(p):
  'phase : COMBAT'
  p[0] = unimplemented()

def p_phase_untap(p):
  'phase : UNTAP'
  p[0] = unimplemented()

def p_phase_upkeep(p):
  '''phase : UPKEEP
           | UPKEEPS'''
  p[0] = unimplemented()

def p_phase_plural(p):
  'phase : phase STEPS'
  p[0] = unimplemented()

def p_time_backref_that(p):
  'time : THAT time'
  p[0] = unimplemented()

def p_time_sorc_cast(p):
  'time : ANY TIME YOU COULD CAST A SORCERY'
  p[0] = unimplemented()

def p_time_ephemeral(p):
  'time : UNTIL time'
  p[0] = unimplemented()

def p_time_before(p):
  'time : BEFORE PLAYING'
  p[0] = unimplemented()

def p_time_eo(p):
  'time : END OF phase'
  p[0] = unimplemented()

def p_time_persistant(p):
  'time : time FOR THE REST OF THE GAME'
  p[0] = unimplemented()

def p_time_till_eot(p):
  'time : time THIS TURN'
  p[0] = unimplemented()

def p_trigger_next(p):
  'time : THE NEXT TIME event'
  p[0] = unimplemented()

def p_time_each(p):
  'time : EACH time'
  p[0] = unimplemented()

def p_time_each_of(p):
  'time : EACH OF time'
  p[0] = unimplemented()

def p_time_upkeep(p):
  'time : object phase'
  p[0] = unimplemented()

def p_time_draw(p):
  'time : object DRAW STEP'
  p[0] = unimplemented()

def p_time_beginning_start(p):
  'time : AT THE BEGINNING OF time'
  p[0] = unimplemented()

def p_time_during(p):
  'time : DURING time'
  p[0] = unimplemented()

def p_time_phase(p):
  'time : phase'
  p[0] = unimplemented()

def p_time_untap(p):
  'time : object UNTAP STEP'
  p[0] = unimplemented()

def p_time_turn(p):
  'time : object TURN'
  p[0] = unimplemented()

def p_time_end_combat(p):
  'time : AT END OF COMBAT'
  p[0] = unimplemented()

def p_etb(p):
  'etb : ENTERS THE BATTLEFIELD'
  p[0] = unimplemented()

def p_ltb_graveyard(p):
  'ltb : IS PUT INTO A GRAVEYARD FROM THE BATTLEFIELD'
  p[0] = unimplemented()

def p_ltb(p):
  'ltb : LEAVES THE BATTLEFIELD'
  p[0] = unimplemented()

def p_when(p):
  'when : WHEN'
  p[0] = unimplemented()

def p_whenever(p):
  'when : WHENEVER'
  p[0] = unimplemented()

def p_trigger_event(p):
  'trigger : IF event'
  p[0] = unimplemented()

def p_trigger_time(p):
  'trigger : time'
  p[0] = unimplemented()

def p_trigger_etb_self(p):
  'trigger : TILDE etb'
  p[0] = unimplemented()

def p_trigger_etb_choice(p):
  'trigger : AS object etb'
  p[0] = unimplemented()

def p_trigger_etb(p):
  'trigger : when object etb'
  p[0] = unimplemented()

def p_trigger_ltb(p):
  'trigger : when object ltb'
  p[0] = unimplemented()

def p_trigger_cast(p):
  'trigger : when object CASTS A color SPELL'
  p[0] = unimplemented()

def p_trigger__mana_tapped(p):
  'trigger : when object IS TAPPED FOR MANA'
  p[0] = unimplemented()

def p_trigger_conditional(p):
  'trigger : trigger WHILE conditional'
  p[0] = unimplemented()

def p_cant(p):
  'cant : CAN APOSTROPHE T'
  p[0] = None

def p_doesnt(p):
  'doesnt : DOESN APOSTROPHE T'
  p[0] = None

def p_dont(p):
  'dont : DON APOSTROPHE T'
  p[0] = None

def p_action_attack(p):
  'action : ATTACKED'
  p[0] = unimplemented()

def p_action_blocked(p):
  'action : BLOCKED'
  p[0] = unimplemented()

def p_conditional(p):
  'conditional : object conditional_part'
  p[0] = unimplemented()

def p_conditional_conjunction(p):
  'conditional_part : conditional_part AND conditional_part'
  p[0] = unimplemented()

def p_contional_or(p):
  'conditional_part : conditional_part OR conditional_part'
  p[0] = unimplemented()

def p_conditional_power(p):
  'conditional_part : POWER math_exp'
  p[0] = unimplemented()

def p_conditional_discard(p):
  'conditional_part : object CAUSES object TO discard object'
  p[0] = unimplemented()

def p_conditional_cyclopean(p):
  'conditional_part : THAT math_exp counter WAS PUT ONTO WITH object'
  p[0] = unimplemented()

def p_conditional_cyclopean_2(p):
  'conditional_part : BUT THAT math_exp counter HAS NOT BEEN REMOVED FROM WITH object'
  p[0] = unimplemented()

def p_conditional_time(p):
  'conditional_part : ATTACKED OR BLOCKED THIS COMBAT'
  p[0] = unimplemented()

def p_conditional_by_type(p):
  'conditional_part : BY type'
  p[0] = unimplemented()

def p_conditional_ante(p):
  'conditional_part : object NOT PLAYING FOR ANTE'
  p[0] = unimplemented()

def p_conditional_untapped(p):
  'conditional_part : IS UNTAPPED'
  p[0] = unimplemented()

def p_conditional_tapped(p):
  'conditional_part : IS TAPPED'
  p[0] = unimplemented()

def p_conditional_action(p):
  'conditional_part : action'
  p[0] = unimplemented()

def p_conditional_backref_action(p):
  'conditional_part : DO'
  p[0] = unimplemented()

def p_conditional_on_battlefield_contraction(p):
  'conditional_part : ON THE BATTLEFIELD' #for it's
  p[0] = unimplemented()

def p_conditional_on_battlefield(p):
  'conditional_part : IS ON THE BATTLEFIELD'
  p[0] = unimplemented()

def p_conditional_has_counter(p):
  'conditional_part : HAS A counter ON IT'
  p[0] = unimplemented()

def p_conditional_never_flipped(p):
  'conditional_part : HAS NOT BEEN TURNED FACE UP'
  p[0] = unimplemented()

def p_conditional_illusory_unflip(p):
  'conditional_part : WOULD ASSIGN OR DEAL DAMAGE COMMA BE DEALT DAMAGE COMMA OR BECOME TAPPED'
  p[0] = unimplemented()

def p_conditional_chaos_orb(p):
  'conditional_part : TURNS OVER COMPLETELY AT LEAST ONCE DURING THE FLIP'
  p[0] = unimplemented()

def p_place_battlefield(p):
  'place : BATTLEFIELD'
  p[0] = unimplemented()

def p_counter_word(p):
  'counter_word : COUNTER'
  p[0] = None

def p_counter_word_plural(p):
  'counter_word : COUNTERS'
  p[0] = None

def p_pt(p):
  'pt : math_exp SLASH math_exp'
  p[0] = unimplemented()

def p_counter_pt_mod(p):
  'counter : pt counter_word'
  p[0] = unimplemented()

def p_counter_mire(p):
  'counter : MIRE counter_word'
  p[0] = unimplemented()

def p_token(p):
  'token_part : pt token_desc CREATURE TOKEN'
  p[0] = unimplemented()

def p_token_with_keyword(p):
  'token : token_part WITH keyword'
  p[0] = unimplemented()

def p_token_no_affect(p):
  'token : token_part'
  p[0] = unimplemented()

def p_token_named(p):
  'token : token NAMED token_name'
  p[0] = unimplemented()

def p_token_named_wasp(p):
  'token_name : WASP'
  p[0] = unimplemented()

def p_token_desc(p):
  'token_desc : token_desc_part'
  p[0] = unimplemented()

def p_token_desc_recur(p):
  'token_desc : token_desc token_desc_part'
  p[0] = unimplemented()

def p_token_color(p):
  'token_desc_part : color'
  p[0] = unimplemented()

def p_token_type(p):
  'token_desc_part : type'
  p[0] = unimplemented()

def p_get(p):
  'get : GET'
  p[0] = unimplemented()

def p_gets(p):
  'get : GETS'
  p[0] = unimplemented()

def p_draw_instruction(p):
  'draw : DRAW'
  p[0] = unimplemented()

def p_draw_present(p):
  'draw : DRAWS'
  p[0] = unimplemented()

def p_keyword_banding(p):
  'keyword : BANDING'
  p[0] = unimplemented()

def p_keyword_defender(p):
  'keyword : DEFENDER'
  p[0] = unimplemented()

def p_keyword_regenerate(p):
  'keyword : REGENERATE object'
  p[0] = unimplemented()

def p_keyword_flying(p):
  'keyword : FLYING'
  p[0] = unimplemented()

def p_keyword_enchant(p):
  'keyword : ENCHANT object'
  p[0] = unimplemented()

def p_keyword_first_strike(p):
  'keyword : FIRST STRIKE'
  p[0] = unimplemented()

def p_keyword_protection(p):
  'keyword : PROTECTION FROM object'
  p[0] = unimplemented()

def p_keyword_swampwalk(p):
  'keyword : SWAMPWALK'
  p[0] = unimplemented()

def p_change_desc_single(p):
  'change_desc : a change_desc'
  p[0] = unimplemented()

def p_change_type(p):
  'change_desc : type'
  p[0] = unimplemented()

def p_change_pt(p):
  'change_desc : pt'
  p[0] = unimplemented()

def p_change_type_chain(p):
  'change_desc : change_desc type'
  p[0] = unimplemented()

def p_change_qualified(p):
  'change_desc : change_desc qualifier'
  p[0] = unimplemented()

def p_being_verb_are(p):
  'being_verb : ARE'
  pass

def p_being_verb_is(p):
  'being_verb : IS'
  pass

def p_being_verb_becomes(p):
  'being_verb : BECOMES'
  pass

def p_have(p):
  'have : HAVE'
  pass

def p_affect_term(p):
  'affect : affect_part'
  p[0] = unimplemented()

def p_affect_recur(p):
  'affect : affect affect_part'
  p[0] = unimplemented()

def p_affect_explicit_conjunction(p):
  'affect : affect AND affect_part'
  p[0] = unimplemented()

def p_affect_conditional_affect(p):
  'affect : affect IF conditional'
  p[0] = unimplemented()

def p_affect_sacrifice(p):
  'affect_part : object SACRIFICES object'
  p[0] = unimplemented()

def p_affect_lose_ability(p):
  'affect_part : object LOSES QUOTE ability QUOTE'
  p[0] = unimplemented()

def p_conjoined_ability_part(p):
  'affect_part : affect_part AND affect_part'
  p[0] = unimplemented()

def p_affect_gain_ability(p):
  'affect_part : object GAINS QUOTE ability QUOTE'
  p[0] = unimplemented()

def p_return(p):
  'affect_part : RETURN object TO zone'
  p[0] = unimplemented()

def p_attach(p):
  'affect_part : ATTACH object TO object'
  p[0] = unimplemented()

def p_affect_dont_untap(p):
  'affect_part : object dont UNTAP'
  p[0] = unimplemented()

def p_affect_no_hand_size(p):
  'affect_part : object have NO MAXIMUM HAND SIZE'
  p[0] = unimplemented()

def p_affect_attacks(p):
  'affect_part : object ATTACKS time IF ABLE'
  p[0] = unimplemented()

def p_affect_schedule_trigger(p):
  'affect_part : trigger COMMA affect'
  p[0] = unimplemented()

def p_affect_pt_mod(p):
  'affect_part : object get math_exp SLASH math_exp'
  p[0] = unimplemented()

def p_affect_becomes_type(p):
  'affect_part : object being_verb change_desc'
  p[0] = unimplemented()

def p_affect_gains_keyword(p):
  'affect_part : object GAINS keyword'
  p[0] = unimplemented()

def p_affect_object_draw(p):
  'affect_part : object draw math_exp card'
  p[0] = unimplemented()

def p_affect_tapped(p):
  'affect_part : TAPPED'
  p[0] = unimplemented()

def p_affect_tap(p):
  'affect_part : TAP object'
  p[0] = unimplemented()

def p_affect_cast_illusory_mask(p):
  'affect_part : CAST object FACE DOWN AS A pt CREATURE SPELL WITHOUT PAYING ITS MANA COST'
  p[0] = unimplemented()

def p_affect_unflip_illusory_mask_creature(p):
  'affect_part : INSTEAD IT APOSTROPHE S TURNED FACE UP AND ASSIGNS OR DEALS DAMAGE COMMA IS DEALT DAMAGE COMMA OR BECOMES TAPPED'
  p[0] = unimplemented()

def p_affect_time_restriction(p):
  'affect_part : FOR AS LONG AS conditional'
  p[0] = unimplemented()

def p_affect_resolve_cost(p):
  'affect_part : PAY cost'
  p[0] = unimplemented()

def p_affect_resolve_optional_affect(p):
  'affect_part : object MAY affect_part'
  p[0] = unimplemented()

def p_ability_static(p):
  'affect_part : affect_part time'
  p[0] = unimplemented()

def p_affect_conditional(p):
  'affect_part : IF conditional COMMA affect'
  p[0] = unimplemented()

def p_affect_counters(p):
  'affect_part : math_exp counter ON object'
  p[0] = unimplemented()

def p_affect_look(p):
  'affect_part : LOOK AT object'
  p[0] = unimplemented()

def p_affect_put_counters(p):
  'affect_part : PUT math_exp counter ON object'
  p[0] = unimplemented()

def p_affect_put_tokens(p):
  'affect_part : PUT math_exp token ONTO THE BATTLEFIELD'
  p[0] = unimplemented()

def p_affect_remove_counters(p):
  'affect_part : REMOVE math_exp counter FROM object'
  p[0] = unimplemented()

def p_affect_remove_card(p):
  'affect_part : REMOVE object FROM zone'
  p[0] = unimplemented()

def p_affect_life_gain(p):
  'affect_part : object GAIN math_exp LIFE'
  p[0] = unimplemented()

def p_affect_prevent_next(p):
  'affect_part : PREVENT THE NEXT math_exp DAMAGE THAT WOULD BE DEALT TO object THIS TURN'
  p[0] = unimplemented()

def p_affect_prevent_backref(p):
  'affect_part : PREVENT math_exp OF THAT DAMAGE'
  p[0] = unimplemented()

def p_affect_destroy(p):
  'affect_part : DESTROY object'
  p[0] = unimplemented()

def p_affect_filp(p):
  'affect_part : FLIP TILDE ONTO THE place FROM A HEIGHT OF AT LEAST ONE FOOT'
  p[0] = unimplemented()

def p_affect_memory(p):
  'affect_part : CHOOSE object'
  p[0] = unimplemented()

def p_affect_stay_tapped(p):
  'affect_part : object doesnt UNTAP'
  p[0] = unimplemented()

def p_affect_untap(p):
  'affect_part : UNTAP object'
  p[0] = unimplemented()

def p_affect_where(p):
  'affect_part : affect_part COMMA WHERE where'
  p[0] = unimplemented()

def p_affect_but(p):
  'affect_part : affect_part COMMA BUT but'
  p[0] = unimplemented()

def p_affect_damage(p):
  'affect_part : object DEALS math_exp DAMAGE TO object'
  p[0] = damage_affect(p[3], p[6])

def p_affect_add_mana_self(p):
  'affect_part : add cost TO YOUR MANA POOL'
  p[0] = unimplemented()

def p_affect_add_mana_object(p):
  'affect_part : object add cost TO object MANA POOL'
  p[0] = unimplemented()

def p_affect_mana_release(p):
  'affect_part : SPEND mana AS THOUGH IT WERE mana'
  p[0] = unimplemented()

def p_affect_discard(p):
  'affect_part : object discard object'
  p[0] = unimplemented()

def p_affect_skip(p):
  'affect_part : SKIP time'
  p[0] = unimplemented()

def p_affect_replacement(p):
  'affect_part : affect_part INSTEAD'
  p[0] = unimplemented()

def p_affect_add_turn(p):
  'affect_part : TAKE math_exp EXTRA TURN AFTER THIS ONE'
  p[0] = unimplemented()

def p_mana_colored(p):
  'mana : color MANA'
  p[0] = unimplemented()

def p_discard(p):
  'discard : DISCARD'
  pass

def p_discards(p):
  'discard : DISCARDS'
  pass

def p_card(p):
  'card : CARD'
  p[0] = unimplemented()

def p_cards(p):
  'card : CARDS'
  p[0] = unimplemented()

def p_add(p):
  'add : ADD'
  p[0] = unimplemented()

def p_adds(p):
  'add : ADDS'
  p[0] = unimplemented()

def p_zone_onto(p):
  'zone : ONTO zone'
  p[0] = unimplemented()

def p_zone_top_library(p):
  'zone : ON TOP OF object LIBRARY'
  p[0] = unimplemented()

def p_zone_graveyard(p):
  'zone : INTO YOUR GRAVEYARD'
  p[0] = unimplemented()

def p_zone_any_graveyard(p):
  'zone : IN A GRAVEYARD'
  p[0] = unimplemented()

def p_zone_battlefield(p):
  'zone : THE BATTLEFIELD'
  p[0] = unimplemented()

def p_zone_deck(p):
  'zone : YOUR DECK'
  p[0] = unimplemented()

def p_zone_controller(p):
  'zone : zone UNDER object CONTROL'
  p[0] = unimplemented()

def p_but_zone_replacement(p):
  'but : object MAY PUT object zone INSTEAD OF zone'
  p[0] = unimplemented()

def p_where(p):
  'where : X IS math_exp'
  p[0] = unimplemented()

def p_math_empty(p):
  'math_exp :'
  p[0] = unimplemented()

def p_math_backref(p):
  'math_exp : THAT'
  p[0] = unimplemented()

def p_math_additional(p):
  'math_exp : math_exp ADDITIONAL'
  p[0] = unimplemented()

def p_math_or_gt(p):
  'math_exp : math_exp OR GREATER'
  p[0] = unimplemented()

def p_math_mt(p):
  'math_exp : MORE THAN math_exp'
  p[0] = unimplemented()

def p_math_gt(p):
  'math_exp : GREATER THAN math_exp'
  p[0] = unimplemented()

def p_math_count(p):
  'math_exp : THE NUMBER OF count'
  p[0] = unimplemented()

def p_math_choose_up_to(p):
  'math_exp : UP TO math_exp'
  p[0] = unimplemented()

def p_math_minus(p):
  'math_exp : math_exp MINUS math_exp'
  p[0] = unimplemented()

def p_math_double_negative(p):
  'math_exp : math_exp BUT math_exp'
  p[0] = unimplemented()

def p_math_unary_plus(p):
  'math_exp : PLUS number'
  p[0] = unimplemented()

def p_math_const(p):
  'math_exp : number'
  p[0] = unimplemented()

def p_count_cards_hand(p):
  'count : CARDS IN object HAND'
  p[0] = unimplemented()

def p_qualifier_top(p):
  'qualifier : qualifier_part'
  p[0] = unimplemented()

def p_qualifier_recur(p):
  'qualifier : qualifier qualifier_part'
  p[0] = unimplemented()

def p_qualifier_enchanted(p):
  'qualifier_part : ENCHANTED'
  p[0] = unimplemented()

def p_qualifier_retain_property(p):
  'qualifier_part : THAT being_verb STILL object'
  p[0] = unimplemented()

def p_qualifier_chaos_orb(p):
  'qualifier_part : IT TOUCHES'
  p[0] = unimplemented()

def p_qualifier_unblocked(p):
  'qualifier_part : math_exp UNBLOCKED'
  p[0] = unimplemented()

def p_qualifier_chosen(p):
  'qualifier_part : OF object CHOICE'
  p[0] = unimplemented()

def p_qualifier_color(p):
  'qualifier_part : color'
  p[0] = unimplemented()

def p_qualifier_card(p):
  'qualifier_part : CARD'
  p[0] = unimplemented()

def p_qualifier_zone(p):
  'qualifier_part : zone'
  p[0] = unimplemented()

def p_qualifier_zone_with(p):
  'qualifier_part : PUT zone WITH object'
  p[0] = unimplemented()

def p_qualifier_held(p):
  'qualifier_part : IN object HAND'
  p[0] = unimplemented()

def p_qualifier_illusory_mask_creature(p):
  'qualifier_part : WHOSE MANA COST COULD BE PAID BY SOME AMOUNT OF COMMA OR ALL OF COMMA THE MANA YOU SPENT ON math_exp'
  p[0] = unimplemented()

def p_qualifier_illusory_mask_creature_resolved(p):
  'qualifier_part : THAT SPELL BECOMES AS IT RESOLVES'
  p[0] = unimplemented()

def p_qualifier_replacement(p):
  'qualifier_part : INSTEAD'
  p[0] = unimplemented()

def p_controller(p):
  'controller : CONTROLLER'
  pass

def p_controllers(p):
  'controller : CONTROLLERS APOSTROPHE'
  pass

def p_object_conditional(p):
  'object : conditional'
  p[0] = unimplemented()

def p_object_with(p):
  'object : object WITH conditional'
  p[0] = unimplemented()

def p_object_num(p):
  'object : math_exp type_list'
  p[0] = unimplemented()

def p_object_backreference(p):
  'object : backref'
  p[0] = unimplemented()

def p_object_backreference_controller(p):
  'object : backref controller'
  p[0] = unimplemented()

def p_object_prequalified_type(p):
  'object : qualifier type'
  p[0] = unimplemented()

def p_object_qualified(p):
  'object : object qualifier'
  p[0] = unimplemented()

def p_object_attribute(p):
  'object : object attribute'
  p[0] = unimplemented()

def p_object_target(p):
  'object : TARGET type_list'
  p[0] = target(p[2])

def p_object_each(p):
  'object : EACH type_list'
  p[0] = unimplemented()

def p_object_self(p):
  'object : TILDE'
  p[0] = unimplemented()

def p_object_all_things_of_color(p):
  'object : color'
  p[0] = unimplemented()

def p_attribute_hand(p):
  'attribute : HAND'
  p[0] = unimplemented()

def p_backref_self(p):
  'backref : '
  p[0] = unimplemented()

def p_backref_chosen_player(p):
  'backref : THE CHOSEN type'
  p[0] = unimplemented()

def p_backref_by_type(p):
  'backref : THE type'
  p[0] = unimplemented()

def p_backref_type(p):
  'backref : THAT type'
  p[0] = unimplemented()

def p_backref_gendered_player(p):
  'backref : HIS OR HER'
  p[0] = unimplemented()

def p_backref_their(p):
  'backref : THEIR'
  p[0] = unimplemented()

def p_backref_it(p):
  'backref : IT'
  p[0] = unimplemented()

def p_backref_your(p):
  'backref : YOUR'
  p[0] = unimplemented()

def p_backref_you(p):
  'backref : YOU'
  p[0] = unimplemented()

def p_backref_its(p):
  'backref : ITS' #english special case of IT APOSTROPHE S
  p[0] = unimplemented()

def p_backref_possessive(p):
  'backref : backref APOSTROPHE S'
  p[0] = unimplemented()

def p_backref_being(p):
  'backref : backref APOSTROPHE RE'
  p[0] = unimplemented()

def p_type_list_term(p):
  'type_list : type'
  p[0] = p[1]

#these help keep commas in line
def p_type_list_3(p):
  'type_list : card_type COMMA card_type COMMA'
  p[0] = unimplemented()

def p_type_list_disjunction(p):
  'type_list : type_list OR card_type'
  p[0] = unimplemented()

def p_type_list_conjunction(p):
  'type_list : type_list AND card_type'
  p[0] = unimplemented()

def p_type_choice(p):
  'type : type OR type'
  p[0] = player_choice(p[1], p[3])

def p_type_exclude(p):
  'type : NON MINUS type type'
  p[0] = unimplemented()

def p_type_effect(p):
  'type : EFFECT'
  p[0] = p[1]

def p_type_permanent(p):
  'type : PERMANENT'
  p[0] = p[1]

def p_type_permanent(p):
  'type : PERMANENTS'
  p[0] = p[1]

def p_type_card(p):
  'type : card'
  p[0] = p[1]

def p_type_damage_source(p):
  'type : SOURCE'
  p[0] = unimplemented()

def p_type_card_type(p):
  'type : card_type'
  p[0] = unimplemented()

def p_type_artifact(p):
  'card_type : ARTIFACT'
  p[0] = unimplemented()

def p_type_artifacts(p):
  'card_type : ARTIFACTS'
  p[0] = unimplemented()

def p_type_creature(p):
  'card_type : CREATURE'
  p[0] = p[1]

def p_type_creatures(p):
  'card_type : CREATURES'
  p[0] = 'CREATURE'

def p_type_land(p):
  'card_type : LAND'
  p[0] = p[1]

def p_type_lands(p):
  'card_type : LANDS'
  p[0] = 'LAND'

def p_type_enchantment(p):
  'card_type : ENCHANTMENT'
  p[0] = p[1]

def p_type_enchantment(p):
  'card_type : ENCHANTMENTS'
  p[0] = 'ENCHANTMENT'

def p_type_golem(p):
  'type : GOLEM'
  p[0] = p[1]

def p_type_insect(p):
  'type : INSECT'
  p[0] = p[1]

def p_type_walls(p):
  'type : WALLS'
  p[0] = 'WALL'

def p_type_spell(p):
  'type : SPELL'
  p[0] = p[1]

def p_type_players(p):
  'type : PLAYER APOSTROPHE S'
  p[0] = unimplemented()

def p_type_player(p):
  'type : PLAYER'
  p[0] = p[1]

def p_type_player_plural(p):
  'type : PLAYERS'
  p[0] = unimplemented()

def p_type_opponent(p):
  'type : OPPONENT'
  p[0] = p[1]

def p_type_swamp(p):
  'type : SWAMP'
  p[0] = p[1]

def p_type_swamps(p):
  'type : SWAMPS'
  p[0] = 'SWAMP'

def p_type_mountain(p):
  'type : MOUNTAIN'
  p[0] = p[1]

def p_type_plains(p):
  'type : PLAINS'
  p[0] = p[1]

def p_type_forest(p):
  'type : FOREST'
  p[0] = p[1]

def p_type_island(p):
  'type : ISLAND'
  p[0] = p[1]

def p_a(p):
  'a : A'
  p[0] = unimplemented()

def p_an(p):
  'a : AN'
  p[0] = unimplemented()

def p_number_num(p):
  'number : NUM'
  p[0] = int(p[1])

def p_number_bracketed(p):
  'number : OPENBRACKET OPENBRACKET OPENBRACKET number CLOSEBRACKET CLOSEBRACKET CLOSEBRACKET'
  p[0] = p[4]

def p_num_all(p):
  'number : ALL'
  p[0] = unimplemented()

def p_num_a(p):
  'number : a'
  p[0] = 1

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
  'cost_part : OPENBRACKET OPENBRACKET OPENBRACKET TAP CLOSEBRACKET CLOSEBRACKET CLOSEBRACKET'
  p[0] = unimplemented()

def p_cost_number(p):
  'cost_part : number'
  p[0] = cost().add_child(p[1])

def p_cost_color(p):
  'cost_part : color'
  p[0] = p[1]

def p_cost_color_bracket(p):
  'cost_part : OPENBRACKET OPENBRACKET OPENBRACKET color CLOSEBRACKET CLOSEBRACKET CLOSEBRACKET'
  p[0] = p[4]

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

def p_color_less(p):
  'color : COLORLESS'
  p[0] = unimplemented()

parser = yacc.yacc(debug=True)

def parse(card_name, card_text):
  return parser.parse(lexer=tokenize(card_name, card_text))

if __name__ == '__main__':
  import MySQLdb
  from password import password
  _conn = MySQLdb.connect (host = "localhost", user = "root", passwd = password, db = "mtg").cursor()
  _conn.execute("SELECT multiverse_id, card_name from `cards` LIMIT 80")
  for id, name in _conn.fetchall():
    _conn.execute("SELECT text from `rules_text` where `card` = %d and flavor = 0" % id)
    for card_text, in _conn.fetchall():
      try:
        parse(name, card_text)
        if DEBUG:
          print name, id
        else:
          print ".",
      except Exception, e:
        print ""
        print name, id
        print '\n'.join(str(x) for x in tokenize(name, card_text))
        raise
