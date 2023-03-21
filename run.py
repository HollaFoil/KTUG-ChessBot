import select
import sys
import socket
import pygame
from pygame.locals import *
from Chess.Board import Board

pygame.init()
 
fps = 60
fpsClock = pygame.time.Clock()
 
width, height = 784, 784
screen = pygame.display.set_mode((width, height))
 
board = Board()

human_mode = False
white_socket_connect = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
black_socket_connect = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Game loop.

#WHITE CONNECTS FIRST
white_socket_connect.bind(('localhost',6969))
white_socket_connect.listen(1)
white_sock, addr = white_socket_connect.accept()

black_socket_connect.bind(('localhost',6970))
black_socket_connect.listen(1)
black_sock, addr = black_socket_connect.accept()

white_sock.setblocking(0)
black_sock.setblocking(0)

white_sock.send(board.generate_fen().encode())

while True:
  screen.fill((0, 0, 0))
  
  for event in pygame.event.get():
    if event.type == QUIT:
      pygame.quit()
      sys.exit()

    if not human_mode:
      break

    if event.type == KEYDOWN:
      if event.key == K_RIGHT:
        board.key_right_event()
      if event.key == K_LEFT:
        board.key_left_event()

    if board.checkmate or board.stalemate:
      break
    if event.type == MOUSEBUTTONDOWN:
      board.on_mouse_down_event()
    if event.type == MOUSEBUTTONUP:
      board.on_mouse_up_event()

  ready_to_read, ready_to_write, in_error = \
               select.select(
                  [white_sock, black_sock],
                  [],
                  [],
                  0.01)

  result = False
  for s_in in ready_to_read:
    data = None
    try:
      data = s_in.recv(1024)
    except:
      print('Connection error')

    if data == None or data == b'':
      continue

    if s_in == white_sock:
      str = data.decode()
      try:
        x1 = ord(str.split()[0][0]) - ord('a')
        y1 = 8 - int(str.split()[0][1])
        x2 = ord(str.split()[1][0]) - ord('a')
        y2 = 8 - int(str.split()[1][1])
        result = board.make_move((x1, y1), (x2, y2))
        print(f'White: {x1=} {y1=} {x2=} {y2=}')
        if not result:
          raise
      except:
        s_in.send(b'ERROR')
        print("Received illegal request by white")
      
    elif s_in == black_sock:
      str = data.decode()
      try:
        x1 = ord(str.split()[0][0]) - ord('a')
        y1 = 8 - int(str.split()[0][1])
        x2 = ord(str.split()[1][0]) - ord('a')
        y2 = 8 - int(str.split()[1][1])
        result = board.make_move((x1, y1), (x2, y2))
        if not result:
          raise
      except:
        s_in.send(b'ERROR')
        print("Received illegal request by black")

  if result:
    sock = white_sock if board.white_to_move else black_sock
    sock.send(board.generate_fen().encode())

  pygame.display.set_caption(board.status)
  screen.blit(board.render_board(), (0,0))
  pygame.display.flip()
  fpsClock.tick(fps)
