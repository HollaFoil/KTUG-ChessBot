#Compile with: pyinstaller --onefile run.py --icon Assets/icon.png --name "ChessBot Board"
import os
import select
import sys
import socket
import pygame
import configparser
import re
from pygame.locals import *
from Chess.Board import Board

pygame.init()
 
fps = 144
fpsClock = pygame.time.Clock()
 
width, height = 1085, 784
screen = pygame.display.set_mode((width, height))
pygame_icon = pygame.image.load("./Assets/icon.png")
pygame.display.set_icon(pygame_icon)
 
board = Board(width, height)

white_sock = None
black_sock = None
white_should_connect = True
black_should_connect = True
readable_sockets = []
is_engine_thinking = False
paused = False

def handle_event(event):
  if event.type == QUIT:
    try:
      white_sock.close()
    except:
      pass
    try:
      black_sock.close()
    except:
      pass
    pygame.quit()
    sys.exit()

  if event.type == K_p:
    paused = not paused
    if is_engine_thinking:
      pass #can implement sending of stop/go commands

  if is_engine_thinking:
    pass

  if event.type == KEYDOWN:
    if event.key == K_RIGHT:
      board.key_right_event()
    if event.key == K_LEFT:
      board.key_left_event()

  if board.is_game_ended():
    return
  if event.type == MOUSEBUTTONDOWN:
    board.on_mouse_down_event()
  if event.type == MOUSEBUTTONUP:
    board.on_mouse_up_event()


pattern = re.compile("([a-h][1-8]){2}")
def sanitize_input(input):
  if len(input) != 4 and len(input) != 5:
    return None
  match = re.match(pattern, input)
  if match == None:
    return None
  x1 = ord(input[0]) - ord('a')
  y1 = 8 - int(input[1])
  x2 = ord(input[2]) - ord('a')
  y2 = 8 - int(input[3])
  piece = ""
  if len(input) == 5:
    piece = input[4]
    if "qnbr".count(piece) < 1:
      return None
  return [(x1, y1), (x2, y2), piece]
  

def send_error(is_white, received = "Unknown"):
  message = "Received illegal request by "
  message += "white" if is_white else "black"
  message += "\nReceived message: " + received
  print(message)
  s_in.send(b'ERROR')


def handle_request(s_in):
  data = None
  is_white = True if s_in == white_sock else False

  if is_white == board.white_to_move:
    board.stop_clock()

  try:
    data = s_in.recv(1024)
  except:
    print('Connection error')
    return False

  if data == None or data == b'':
    return False

  print("Received message from " + ("white: " if is_white else "black: ") + data.decode())

  move = sanitize_input(data.decode())
  if move == None:
    send_error(is_white, data.decode())
    return False

  result = board.make_move(move[0], move[1], move[2])
  if not result:
    send_error(is_white, data.decode())
  return result


def send_fen():
  s_in = white_sock if board.white_to_move else black_sock
  if s_in == None:
    return

  print("Sending fen to " + "white" if s_in == white_sock else "black")
  global is_engine_thinking
  is_engine_thinking = True
  fen = board.generate_fen()
  s_in.send(fen.encode())


def connect():
  global white_should_connect
  global black_should_connect
  global white_sock
  global black_sock
  global readable_sockets

  white_socket_connect = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  black_socket_connect = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

  white_socket_connect.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  black_socket_connect.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

  white_socket_connect.bind(('localhost',6969))
  black_socket_connect.bind(('localhost',6970))

  if white_should_connect:
    print("Waiting for white to connect...")
    white_socket_connect.listen(1)
    white_sock, _ = white_socket_connect.accept()
    white_should_connect = False
    print("White connected!")
  if black_should_connect:
    print("Waiting for black to connect...")
    black_socket_connect.listen(1)
    black_sock, _ = black_socket_connect.accept()
    black_should_connect = False
    print("Black connected!")

  if white_sock != None:
    white_sock.setblocking(0)
    readable_sockets += [white_sock]
  if black_sock != None:
    black_sock.setblocking(0)
    readable_sockets += [black_sock]


def query_should_connect():
  global white_should_connect
  global black_should_connect
  config = configparser.ConfigParser()
  should_always_ask = False
  try:
    if os.path.exists("config.txt"):
      config.read("config.txt")
      if config.getboolean("LAUNCH SETTINGS", "Should_Always_Ask"):
        should_always_ask = True
        raise
      white_should_connect = config.getboolean("LAUNCH SETTINGS", "White_Is_Engine")
      black_should_connect = config.getboolean("LAUNCH SETTINGS", "Black_Is_Engine")
      return
  except:
    pass

  while True:
    print("Is white an engine? (y/n): ", end='')
    answer = input()
    if answer != "y" and answer != "n":
      print("Invalid answer")
      continue
    white_should_connect = (answer == "y")
    break

  while True:
    print("Is black an engine? (y/n): ", end='')
    answer = input()
    if answer != "y" and answer != "n":
      print("Invalid answer")
      continue
    black_should_connect = (answer == "y")
    break
  config["LAUNCH SETTINGS"] = {'White_Is_Engine': white_should_connect, 
                               'Black_Is_Engine': black_should_connect,
                               'Should_Always_Ask': should_always_ask}
  with open("config.txt", 'w') as configfile:
    config.write(configfile)


def init():
  query_should_connect()

  try:   
    connect()
  except:
    print("Failed to connect engines")
    input()
    exit()


def render():
  screen.fill((50, 50, 50))
  pygame.display.set_caption(board.status)
  screen.blit(board.render_board(), (0,0))
  pygame.display.flip()
  fpsClock.tick(fps)


render()
print("Initializing game")
init()
send_fen()
print("Game starting!")
while True:
  for event in pygame.event.get():
    handle_event(event)

  ready_to_read = []
  if readable_sockets != []:
    ready_to_read, _, _ = select.select(readable_sockets, [], [], 0.01)

  for s_in in ready_to_read:
    result = handle_request(s_in)
    if result:
      is_engine_thinking = False
    else:
      board.start_clock()

  if not is_engine_thinking and not board.is_clock_ticking:
    board.start_clock()

  if board.should_send_fen and not board.is_game_ended():
    send_fen()
    board.start_clock()
    board.should_send_fen = False

  board.tick_clock()
  render()

