import pygame
import backend
import time
import re
import asyncio

def draw_x(surface, color, circle_center, circle_radius, thicc):
    x1 = circle_center[0] - int(circle_radius * 0.707)  # 0.707 is roughly cos(45) or sin(45)
    y1 = circle_center[1] - int(circle_radius * 0.707)
    x2 = circle_center[0] + int(circle_radius * 0.707)
    y2 = circle_center[1] + int(circle_radius * 0.707)

    x3 = circle_center[0] + int(circle_radius * 0.707)
    y3 = circle_center[1] - int(circle_radius * 0.707)
    x4 = circle_center[0] - int(circle_radius * 0.707)
    y4 = circle_center[1] + int(circle_radius * 0.707)

    pygame.draw.line(surface, color, (x1, y1), (x2, y2), thicc)
    pygame.draw.line(surface, color, (x3, y3), (x4, y4), thicc)

class InputBox:
    def __init__(self, x, y, w, h, color_active, color_inactive, font, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = color_inactive
        self.text = text
        self.txt_surface = font.render(text, True, self.color)
        self.active = False
        self.remove_default_text = True
        self.color_active = color_active
        self.color_inactive = color_inactive
        self.font = font

    def process_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect.
            if self.rect.collidepoint(event.pos):
                # Toggle the active variable.
                self.active = not self.active
                if self.remove_default_text:
                    self.text = ""
                    self.remove_default_text = False
                    # Re-render the text.
                    self.txt_surface = self.font.render(self.text, True, self.color)
            else:
                self.active = False
            # Change the current color of the input box.
            self.color = self.color_active if self.active else self.color_inactive
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    pass
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                # Re-render the text.
                self.txt_surface = self.font.render(self.text, True, self.color)

    def update(self):
        # Resize the box if the text is too long.
        width = max(self.rect.w, self.txt_surface.get_width()+10)
        self.rect.w = width

    def render(self, screen):
        # Blit the text.
        screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))
        # Blit the rect.
        pygame.draw.rect(screen, self.color, self.rect, 2)

class Button:
    def __init__(self, x, y, w, h, button_color, text_color, font, text):
        self.color = button_color
        self.rect = pygame.Rect(x, y, w, h)
        self.text = font.render(text, True, text_color)

    def render(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        screen.blit(self.text, (self.rect.x + 15, self.rect.y + 10))

class BaseScene:
    def __init__(self, field, screen_size):
        self.field = field
        self.screen_size = screen_size
        self.radius = 40
        self.next_scene = self

    def process_input(self, events):
        pass

    def update(self):
        pass

    def render(self, screen):
        pass

    def switch_to(self, next_scene):
        self.next_scene = next_scene

class ChooseStone(BaseScene):
    def __init__(self, field, screen_size):
        super().__init__(field, screen_size)
        self.circle_center = self.screen_size * 3 / 4, self.screen_size / 2
        self.x_center = self.screen_size / 4, self.screen_size / 2

    def process_input(self, events):
        self.left_click_event = None
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:    
                if event.button == 1:
                    self.left_click_event = event

    def update(self):
        if self.left_click_event is not None:
            if self.left_click_event.pos[0] < self.screen_size / 2:
                self.field.player_char = "x"
            else:
                self.field.player_char = "o"
            self.switch_to(ChooseSizes(self.field, self.screen_size))
        self.mouse_pos = pygame.mouse.get_pos()

    def render(self, screen):
        rect1 = pygame.draw.rect(screen, "black", (0, 0, self.screen_size / 2, self.screen_size))
        rect2 = pygame.draw.rect(screen, "black", (self.screen_size / 2, 0, self.screen_size / 2, self.screen_size))

        if pygame.Rect.collidepoint(rect1, self.mouse_pos):
            pygame.draw.rect(screen, "dodgerblue4", (0, 0, self.screen_size / 2, self.screen_size))
            draw_x(screen, "white", self.x_center, self.radius, 20)
            pygame.draw.circle(screen, "white", self.circle_center, self.radius, 5)
        elif pygame.Rect.collidepoint(rect2, self.mouse_pos):
            pygame.draw.rect(screen, "firebrick3", (self.screen_size / 2, 0, self.screen_size / 2, self.screen_size))
            draw_x(screen, "white", self.x_center, self.radius, 5)
            pygame.draw.circle(screen, "white", self.circle_center, self.radius, 20)

class ChooseSizes(BaseScene):
    def __init__(self, field, screen_size):
        super().__init__(field, screen_size)
        self.box_width = 50
        self.box_height = 32
        self.box_gap = 40
        self.box_margin = 5
        self.center = (screen_size // 2, screen_size * 1 / 4)
        self.form_center = (screen_size // 2, screen_size // 2)

        self.font = pygame.font.Font(None, 32)
        self.bs = self.font.render("Board size (1-50):", True, "white")
        self.sir = self.font.render("Stones in row (1-10):", True, "white")

        self.color_inactive = 'black'
        self.color_active = 'white'
        self.input_boxes = [
            InputBox(self.form_center[0] - self.box_width, self.form_center[1] - self.box_height, self.box_width, self.box_height,
                     self.color_active, self.color_inactive, self.font, "5"),
            InputBox(self.form_center[0] - self.box_width, self.form_center[1] - self.box_height + self.box_gap, self.box_width, self.box_height,
                     self.color_active, self.color_inactive, self.font, "3")
        ]

        self.button = Button(self.form_center[0] - self.box_width, self.form_center[1] - self.box_height + 2 * self.box_gap, 80, 40, "black", "white", self.font, "Start")

    def process_input(self, events):
        self.button_clicked_event = None
        for event in events:
            for box in self.input_boxes:
                box.process_input(event)
            if event.type == pygame.MOUSEBUTTONDOWN:  
                if event.button == 1:
                    if self.button.rect.collidepoint(event.pos):
                        self.button_clicked_event = event
    
    def update(self):
        for box in self.input_boxes:
            box.update()
        if self.button_clicked_event is not None:
            if (a := re.search(r"(\d+)", self.input_boxes[0].text)) is not None and (b := re.search(r"(\d+)", self.input_boxes[1].text)) is not None:
                m = int(a.group(1))
                k = int(b.group(1))
                if m >= 1 or m <= 50 or k >= 1 or k <= 10:
                    self.field.m = m
                    self.field.k = k
                    self.switch_to(MainScene(self.field, self.screen_size))

    def render(self, screen):
        if self.field.player_char == "x":
            pygame.draw.rect(screen, "dodgerblue4", (0, 0, self.screen_size, self.screen_size))
            draw_x(screen, "white", self.center, self.radius, 20)
        elif self.field.player_char == "o":
            pygame.draw.rect(screen, "firebrick3", (0, 0, self.screen_size, self.screen_size))
            pygame.draw.circle(screen, "white", self.center, self.radius, 20)

        screen.blit(self.bs, (self.form_center[0] - 6 * self.box_width, self.form_center[1] - self.box_height + self.box_margin))
        screen.blit(self.sir, (self.form_center[0] - 6 * self.box_width, self.form_center[1] - self.box_height + self.box_margin + self.box_gap))

        for box in self.input_boxes:
            box.render(screen)
        
        self.button.render(screen)

class MainScene(BaseScene):
    def __init__(self, field, screen_size):
        super().__init__(field, screen_size)
        self.cell_size = screen_size // self.field.m
        self.outer_border = (screen_size % self.field.m) // 2
        self.border = 2
        self.radius = self.cell_size // 3
        self.thicc = self.cell_size // 10
        self.offset = (self.cell_size - self.border) // 2
        self.winning_indices = []

        field.generate_from_input()
    
    def process_input(self, events):
        self.cell_clicked_event = None
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:    
                if event.button == 1:
                    self.cell_clicked_event = event

    def update(self):
        if self.winning_indices:
            self._new_round()
        # Game is afoot!
        if self.field.possible_moves:
            if self.field.player_turn:
                if self.cell_clicked_event is not None:
                    row = (self.cell_clicked_event.pos[1] - self.outer_border) // self.cell_size
                    col = (self.cell_clicked_event.pos[0] - self.outer_border) // self.cell_size
                    if self.field.is_cell_free(row, col):
                        self.field.put_char_on_field(row, col)
                        self.field.change_turn()
            else:
                backend.computer_move(self.field)
                time.sleep(0.5)
            if (winner_char_and_indices := backend.get_winner(self.field.cells, self.field.k)) is not None:
                self.winning_indices = winner_char_and_indices[1]
        else:
            # Tie
            self._new_round()
    
    def render(self, screen):
        screen.fill("black")
        for i, row in enumerate(self.field.cells):
            for j, cell in enumerate(row):
                rect_left = j * self.cell_size + 1 + self.outer_border
                rect_top = i * self.cell_size + 1 + self.outer_border

                pygame.draw.rect(screen, "white", (rect_left, rect_top, self.cell_size - self.border, self.cell_size - self.border))
                if self.winning_indices and cell[1] in self.winning_indices:
                    pygame.draw.rect(screen, "green", (rect_left, rect_top, self.cell_size - self.border, self.cell_size - self.border))

                center = (rect_left + self.offset , rect_top + self.offset)
                if cell[0] == "x":
                    draw_x(screen, "blue", center, self.radius, self.thicc)
                elif cell[0] == "o":
                    pygame.draw.circle(screen, "red", center, self.radius, self.thicc)
    
    def _new_round(self):
        time.sleep(2)
        self.field.player_turn = self.field.player_char == "x"
        self.field.generate_from_input()
        self.winning_indices = []

async def main():
    SCREEN_SIZE = 800

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
    clock = pygame.time.Clock()

    active_scene = ChooseStone(backend.Field(), SCREEN_SIZE)
    run = True
    while run:
        # Events
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                run = False 
            
        active_scene.process_input(events)
        active_scene.update()
        active_scene.render(screen)
        active_scene = active_scene.next_scene

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

if __name__ == "__main__":
    args = backend.get_args()
    if args.term:
        backend.terminal_main(args)
    else:
        asyncio.run(main())
        pygame.quit()