import tkinter as tk
from enum import Enum


import cv2 as cv
import numpy as np


class GameObject(object):
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)


class Ball(GameObject):
    def __init__(self, canvas, x, y):
        self.radius = 10
        self.direction = [1, -1]
        # increase the below value to increase the speed of ball
        self.speed = 5
        item = canvas.create_oval(x - self.radius, y - self.radius,
                                  x + self.radius, y + self.radius,
                                  fill='white')
        super(Ball, self).__init__(canvas, item)

    def update(self):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] <= 0 or coords[2] >= width:
            self.direction[0] *= -1
        if coords[1] <= 0:
            self.direction[1] *= -1
        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)

    def collide(self, game_objects):
        coords = self.get_position()
        x = (coords[0] + coords[2]) * 0.5
        if len(game_objects) > 1:
            self.direction[1] *= -1
        elif len(game_objects) == 1:
            game_object = game_objects[0]
            coords = game_object.get_position()
            if x > coords[2]:
                self.direction[0] = 1
            elif x < coords[0]:
                self.direction[0] = -1
            else:
                self.direction[1] *= -1

        for game_object in game_objects:
            if isinstance(game_object, Brick):
                game_object.hit()


class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.width = 80
        self.height = 10
        self.ball = None
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill='#FFB643')
        super(Paddle, self).__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def move(self, offset):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] + offset >= 0 and coords[2] + offset <= width:
            super(Paddle, self).move(offset, 0)
            if self.ball is not None:
                self.ball.move(offset, 0)


class Brick(GameObject):
    COLORS = {1: '#4535AA', 2: '#ED639E', 3: '#8FE1A2'}

    def __init__(self, canvas, x, y, hits):
        self.width = 75
        self.height = 20
        self.hits = hits
        color = Brick.COLORS[hits]
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill=color, tags='brick')
        super(Brick, self).__init__(canvas, item)

    def hit(self):
        self.hits -= 1
        if self.hits == 0:
            self.delete()
        else:
            self.canvas.itemconfig(self.item,
                                   fill=Brick.COLORS[self.hits])


class Game(tk.Frame):
    def __init__(self, master):
        super(Game, self).__init__(master)
        self.lives = 3
        self.width = 610
        self.height = 400
        self.canvas = tk.Canvas(self, bg='#D6D1F5',
                                width=self.width,
                                height=self.height, )
        self.canvas.pack()
        self.pack()

        self.items = {}
        self.ball = None
        self.paddle = Paddle(self.canvas, self.width / 2, 326)
        self.items[self.paddle.item] = self.paddle

        self.camInput = camInput()

        # adding brick with different hit capacities - 3,2 and 1
        for x in range(5, self.width - 5, 75):
            self.add_brick(x + 37.5, 50, 3)
            self.add_brick(x + 37.5, 70, 2)
            self.add_brick(x + 37.5, 90, 1)

        self.hud = None
        self.setup_game()
        self.canvas.focus_set()

    def setup_game(self):
        self.camInput.destroyWindow()
        self.add_ball()
        self.update_lives_text()
        self.text = self.draw_text(300, 200,
                                   'Press Space to start')
        self.canvas.bind('<space>', lambda _: self.start_game())

    def add_ball(self):
        if self.ball is not None:
            self.ball.delete()
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        self.ball = Ball(self.canvas, x, 310)
        self.paddle.set_ball(self.ball)

    def add_brick(self, x, y, hits):
        brick = Brick(self.canvas, x, y, hits)
        self.items[brick.item] = brick

    def draw_text(self, x, y, text, size='40'):
        font = ('Forte', size)
        return self.canvas.create_text(x, y, text=text,
                                       font=font)

    def update_lives_text(self):
        text = 'Lives: %s' % self.lives
        if self.hud is None:
            self.hud = self.draw_text(50, 20, text, 15)
        else:
            self.canvas.itemconfig(self.hud, text=text)

    def start_game(self):

        self.camInput.showcam()

        self.canvas.unbind('<space>')
        self.canvas.delete(self.text)
        self.paddle.ball = None
        self.game_loop()


    def game_loop(self):

        self.camInput.object_detection()

        MovementDirection = self.camInput.position

        if MovementDirection == MovementDirection.LEFT:
            self.paddle.move(-12)
        elif MovementDirection == MovementDirection.RIGHT:
            self.paddle.move(12)

        self.check_collisions()
        num_bricks = len(self.canvas.find_withtag('brick'))
        if num_bricks == 0:
            self.camInput.destroyWindow()
            self.ball.speed = None
            self.draw_text(300, 200, 'You win! You the Breaker of Bricks.')
        elif self.ball.get_position()[3] >= self.height:
            self.ball.speed = None
            self.lives -= 1
            if self.lives < 0:
                self.camInput.destroyWindow()
                self.draw_text(300, 200, 'You Lose! Game Over!')
            else:
                self.after(1000, self.setup_game)
        else:
            self.ball.update()
            self.after(50, self.game_loop)

    def check_collisions(self):
        ball_coords = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items[x] for x in items if x in self.items]
        self.ball.collide(objects)


class camInput:

    def __init__(self):
        self.cam = cv.VideoCapture()


    def showcam(self):
        if not self.cam.isOpened():
            self.cam.open(0)

    def object_detection(self):
        cam = self.cam
        ret, image = cam.read()
        image = image[:, ::-1, :]

        fullmask = self.cammask(image)
        contours, ret = cv.findContours(fullmask, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
        countourIdx = self.countouridx(contours)  #coordenadas dos pixesi

        image_copy = image.copy()
        cv.drawContours(image=image_copy, contours=contours, contourIdx=countourIdx, color=(30, 255, 255), thickness=-1)
        cv.imshow("CameraObject", image_copy)

        if countourIdx > -1:
            self.position = self.positionside(image_copy, contours[countourIdx])
        else:
            self.position = MovementDirection.MIDDLE

    def cammask(self, image):
        blur= cv.GaussianBlur(image,(25,25),0)
        hsv = cv.cvtColor(blur, cv.COLOR_BGR2HSV) #converter BRG -> HSV
        return cv.inRange(hsv, np.array([20, 100, 100]), np.array([30, 255, 255]))

    def positionside(self, image, countour):
        position = MovementDirection.MIDDLE
        contour_center = self.contourcenter(countour)
        x_image_center = image.shape[1] / 2



        if (contour_center[0] > x_image_center - 20) & (contour_center[0] < x_image_center + 20):
            position = MovementDirection.MIDDLE
        elif contour_center[0] > x_image_center +20:
            position = MovementDirection.RIGHT
        elif contour_center[0] < x_image_center - 20:
            position = MovementDirection.LEFT

        return position

    def contourcenter(self, contour):
        moment = cv.moments(contour)
        x = int(moment["m10"] / moment["m00"])
        y = int(moment["m01"] / moment["m00"])
        return [x, y]

    def countouridx(self, contours):
        countour_idx = -1
        max_area = 0

        for i in range(len(contours)):
            current_contour = contours[i]
            countour_area = cv.contourArea(current_contour)
            if countour_area > max_area:
                max_area = countour_area
                countour_idx = i


        return countour_idx

    def destroywindow(self):
        cam = self.cam

        if cam.isOpened():
            cam.release()
            cv.destroyWindow("CameraObject")


class MovementDirection(Enum):
    LEFT = 0
    MIDDLE = 1
    RIGHT = 2


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Break those Bricks!')
    game = Game(root)
    game.mainloop()
