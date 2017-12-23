#! python
# -*- coding: utf-8 -*-

#---------------------------------------
# [Required] Script Information
#---------------------------------------
ScriptName = "cryptoTrading"
Website = "No Website at the moment"
Description = "Cryto Trading extension lets viewers spend loyalty points on pretend cryptos."
Creator = "Verboss1"
Version = "0.1"

import sys
import os
import clr
clr.AddReference("IronPython.SQLite.dll")
clr.AddReference("IronPython.Modules.dll")
import json
import sqlite3 as lite
import ast

#---------------------------------------
# Set Variables
#---------------------------------------
m_CooldownSeconds = 10
m_CommandPermission = "Everyone"
m_CommandInfo = ""

USERNAME = ""
command_map = []
SUPPORTED_COINS = ["BTC", "ETH", "LTC"]
CURRENCY_NAME = ""

EX_CRYPTO     = "!crypto"
EX_PRICE      = "!price <btc,eth,ltc>"
EX_BUY        = "!buy <btc,eth,ltc> <quantity>"
EX_SELL       = "!sell <btc,eth,ltc> <quantity>"
EX_PORTFOLIO  = "!portfolio"
EX_COIN       = "!coin"

EX_COMMANDS   = " | ".join((EX_CRYPTO, EX_PRICE, EX_BUY, EX_SELL, EX_PORTFOLIO, EX_COIN))

# Handle for sql calls
db_name = 'holdings.db'
local_db_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), db_name)
cur = 0

def requires_db_connection(func):
  """
  Opens connection to the database
  and closes once transaction is done
  """
  def wrapper(args):
    global cur
    with lite.connect(local_db_path) as con:
      cur = con.cursor()
      func(args)
  return wrapper

def has_n_args(args, n):
  if len(args) != n:
    return False;
  return 

def requires_3_args(func):
  def wrapper(args):
    if len(args) < 3:
      print "Error: command requires 3 arguments and only called with " + str(len(args))
      return
    else:
      return func(args)
  return wrapper

@requires_db_connection
def run_query(query):
  try:
    cur.execute(query)
  except lite.Error as e:
    print "Trainsaction failed"
    raise e
  except Exception as e:
    print "Unhandled exception, bailing out"
    raise e 

'''
Returns: str of supported coins
'''
#
def get_supported_coins():
  coins = ""
  for c in SUPPORTED_COINS:
    coins = coins + " " + c
  return coins

def is_supported_coin(coin):
  return coin in SUPPORTED_COINS


'''
Brief: Provides price of a coin
in:
  str coin
out:
  float
'''
def get_price(coin):
  if coin not in SUPPORTED_COINS:
    print "Error: coin " + coin + " is not supported."
    return
    
  DummyHeaders = {}
  query = "https://api.coinbase.com/v2/prices/" + str(coin) + "-USD/buy"
  
  # GET Request API endpoint
  response = Parent.GetRequest(query, DummyHeaders)
  # Parse the response (to extract status and response)
  reponseObj = json.loads(response)

  # if status 200 : success
  if reponseObj["status"] == 200:
    result = json.loads(reponseObj['response'])
    return float(result['data']['amount'])

def cmd_price_check(args):
  # value checking
  try:
    if len(args) < 2 or not args[1].isalpha():
      raise ValueError("Incorrect format of input")
    coin = args[1].upper()
  except ValueError as e:
    Parent.SendTwitchMessage(USERNAME + ", incorrect format. Use: " + EX_PRICE)
    return
  
  try:
    if not args[1].isalpha() :
      raise ValueError("Incorrect format of input")
    coin = args[1].upper()
  except ValueError as e:
    Parent.SendTwitchMessage(USERNAME + ", incorrect format. Use: " + EX_PRICE)
    return
  
  if not is_supported_coin(coin):
    Parent.SendTwitchMessage("Error: coin is not supported - " + coin)
    return
  
  price = get_price(coin)
  msg = "Current price of " + coin + ": " + str(price) + " " + CURRENCY_NAME + "."
  Parent.SendTwitchMessage(msg)

def cmd_buy(args):
  # value checking
  try:
    if len(args) < 3 or not args[1].isalpha():
      raise ValueError("Incorrect format of input")
    coin = args[1].upper()
    txn_qty = float(args[2])
  except ValueError as e:
    Parent.SendTwitchMessage(USERNAME + ", incorrect format. Use: " + EX_BUY)
    return
  
  if txn_qty <= 0.0:
    Parent.SendTwitchMessage(USERNAME + ", you must buy more than 0")
    return
  
  if not is_supported_coin(coin):
    Parent.SendTwitchMessage("Error: coin is not supported - " + coin)
    return
    
  coin_price = get_price(coin)
  txn_cost = coin_price * txn_qty
  
  if Parent.RemovePoints(USERNAME, long(txn_cost)):
    # First attempt to insert entry
    query = "INSERT INTO Holds VALUES('" + USERNAME + "', '" + coin + "', " + str(txn_qty) + ")"
    update_required = False
    try:
      run_query(query)
    except lite.Error:
      update_required = True
    except:
      print "Not runtime..."
    
    if update_required:
      query = "UPDATE Holds SET qty = qty + " + str(txn_qty) + \
              " WHERE Name = '" + USERNAME + "' and COIN = '" + coin + "'"
      run_query(query)
      
    #Success, notify user of purchase
    msg = USERNAME + " has purchased " + str(txn_qty) + " " + coin + " for " + str(txn_cost) + " " + CURRENCY_NAME
  else:
    msg = USERNAME + " does not have sufficient funds to purchase " + str(txn_qty) + " " + coin + "."
  
  Parent.SendTwitchMessage(msg)

def cmd_sell(args):
  # value checking
  try:
    if len(args) < 3 or not args[1].isalpha():
      raise ValueError("Incorrect format of input")
    coin = args[1].upper()
    txn_qty = float(args[2])
  except ValueError as e:
    Parent.SendTwitchMessage(USERNAME + ", incorrect format. Use: " + EX_SELL)
    return
  
  if txn_qty <= 0:
    Parent.SendTwitchMessage(USERNAME + ", you must sell more than 0")
    return
  
  if not is_supported_coin(coin):
    Parent.SendTwitchMessage("Error: coin is not supported - " + coin)
    return
  
  # Retrieve amount user has of this coin
  query = "SELECT qty from holds where name='" + USERNAME + "' and coin='" + coin + "'"
  run_query(query)
  
  res = cur.fetchall()
  
  if not res:
    Parent.SendTwitchMessage(USERNAME + " is not holding any " + coin)
    return
    
  user_qty = float(res[0][0])
  print "user_qty: " + str(user_qty)
  if user_qty < txn_qty:
    Parent.SendTwitchMessage(USERNAME + ", you cannot sell more than you hold.")
    return
  
  #else continue and sell
  coin_price = get_price(coin)
  txn_cost = txn_qty * coin_price
  
  if txn_qty == user_qty:
    # Delete entry
    query = "DELETE from holds where name = '" + USERNAME + "' and coin = '" + coin + "'"
    run_query(query)
  else:
    # Update entry with difference
    new_qty = user_qty - txn_qty
    query = "UPDATE Holds SET qty = " + str(new_qty) + \
              " WHERE Name = '" + USERNAME + "' and COIN = '" + coin + "'"
    run_query(query)
  
  msg = USERNAME + " has sold " + str(txn_qty) + " " + coin + " for " + str(txn_cost) + " " + CURRENCY_NAME
  Parent.AddPoints(USERNAME, txn_cost)
  Parent.SendTwitchMessage(msg)

def cmd_portfolio(args):
  query = "SELECT coin, qty  from Holds WHERE Name = '" + USERNAME + "'"
  run_query(query)
  p = cur.fetchall()
  if len(p) < 1:
    portfolio_msg = USERNAME + " currently is not holding any coin."
  else:
    portfolio_msg = USERNAME + "'s holdings: "
    for c in p:
      portfolio_msg = portfolio_msg + c[0] + ':' + str(c[1]) + " "
  Parent.SendTwitchMessage(portfolio_msg)
  print portfolio_msg

def cmd_crypto(args):
  msg = "Current list of cryptoTrading commands: " + EX_COMMANDS
  Parent.SendTwitchMessage(msg)

def cmd_coin(args):
  msg = "Supported coins: " + " | ".join(SUPPORTED_COINS)
  Parent.SendTwitchMessage(msg)

def create_db():
  query = "CREATE TABLE Holds(Name TEXT, Coin TEXT, Qty DOUBLE(32,8), PRIMARY KEY (Name, Coin))"
  run_query(query)

#---------------------------------------
# [Required] Intialize Data (Only called on Load)
#---------------------------------------
def Init():
  global command_map
  global CURRENCY_NAME
  # setup commands
  command_map = {"!price"      : cmd_price_check,
                 "!buy"        : cmd_buy,
                 "!sell"       : cmd_sell,
                 "!portfolio"  : cmd_portfolio,
                 "!crypto"     : cmd_crypto,
                 "!coin"       : cmd_coin
  }
  
  CURRENCY_NAME = Parent.GetCurrencyName()
  
  # If DB does not exist, create it
  if not os.path.isfile(local_db_path):
    create_db()
  
#---------------------------------------
# [Required] Execute Data / Process Messages
#---------------------------------------
def Execute(data):
  global USERNAME
  if data.IsChatMessage():
    user_cmd = data.GetParam(0).lower()
    if user_cmd in command_map.keys() and \
       not Parent.IsOnCooldown(ScriptName,user_cmd) and \
       Parent.HasPermission(data.User,m_CommandPermission,m_CommandInfo):
      
      USERNAME = data.User
      user_msg = data.Message.split();
      command_map[user_cmd](user_msg)
      
  return

#---------------------------------------
# [Required] Tick Function
#---------------------------------------
def Tick():
  return

# main()