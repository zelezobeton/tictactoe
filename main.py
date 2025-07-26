"""
TODO:
- Merge the code between backend and frontend
- Make command line option with input arguments and choice if I want to use graphics or terminal as interface
- Try to find good design pattern in the project

DONE:
- Xs and Os in higher size grids (ie > 20) have uneven margin in cell (small Xs are still off but I don't care anymore)
- Black border is uneven for some grid sizes, 30 for example. Maybe fix dividing?
- Bug when I fill first form field and only click on second, start button won't work
"""

import pygame
import backend
import time
import re
import asyncio

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

    def handle_event(self, event):
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

    def draw(self, screen):
        # Blit the text.
        screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))
        # Blit the rect.
        pygame.draw.rect(screen, self.color, self.rect, 2)

class Button():
    def __init__(self, x, y, w, h, button_color, text_color, font, text):
        self.color = button_color
        self.rect = pygame.Rect(x, y, w, h)
        self.text = font.render(text, True, text_color)

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

def new_round(winning_indices, field_cells, possible_moves, player_turn, grid_size):
    winning_indices = []
    field_cells, possible_moves = backend.generate_field(grid_size)
    time.sleep(2)
    player_turn = True
    return winning_indices, field_cells, possible_moves, player_turn

async def main():
    SCREEN_SIZE = 800

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
    clock = pygame.time.Clock()

    color_inactive = pygame.Color('black')
    color_active = pygame.Color('white')
    font = pygame.font.Font(None, 32)

    grid_size = None
    k = None
    button = None
    input_boxes = []
    player_char = None
    computer_char = None
    player_turn = True
    winning_indices = []
    field_cells = possible_moves = None
    scene1 = True
    scene2 = scene3 = False
    run = True
    while run:
        # Events
        cell_clicked_event = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False 
            if event.type == pygame.MOUSEBUTTONDOWN:    
                if event.button == 1:
                    cell_clicked_event = event
                if button is not None:
                    if button.rect.collidepoint(event.pos):
                        if (m := re.search(r"(\d+)", input_boxes[0].text)) is not None and (n := re.search(r"(\d+)", input_boxes[1].text)) is not None:
                            grid_size = int(m.group(1))
                            k = int(n.group(1))
                            if grid_size < 1 or grid_size > 50 or k < 1 or k > 10:
                                continue
                            scene2 = False
                            scene3 = True
                            cell_clicked_event = None
                            input_boxes = []
                            button = None
                        
            for box in input_boxes:
                box.handle_event(event)
            
        # Logic
        for box in input_boxes:
            box.update()
        if scene3:
            cell_size = SCREEN_SIZE // grid_size
            outer_border = (SCREEN_SIZE % grid_size) // 2
            if field_cells is None and possible_moves is None:
                field_cells, possible_moves = backend.generate_field(grid_size)
            if winning_indices:
                winning_indices, field_cells, possible_moves, player_turn = new_round(winning_indices, field_cells, possible_moves, player_turn, grid_size)
            if possible_moves:
                if player_turn:
                    if cell_clicked_event is not None:
                        row = (cell_clicked_event.pos[1] - outer_border) // cell_size
                        col = (cell_clicked_event.pos[0] - outer_border) // cell_size
                        if field_cells[row][col][0] is None:
                            field_cells[row][col][0] = player_char
                            possible_moves.remove((row, col))
                            player_turn = not player_turn
                else:
                    backend.computer_move(possible_moves, computer_char, field_cells, player_char, grid_size, k)
                    player_turn = not player_turn
                    time.sleep(0.5)
            else:
                winning_indices, field_cells, possible_moves, player_turn = new_round(winning_indices, field_cells, possible_moves, player_turn, grid_size)
            if (winner_char_and_indices := backend.get_winner(field_cells, k)) is not None:
                winning_indices = winner_char_and_indices[1]
        
        # Graphics
        screen.fill("black")
        circle_center = SCREEN_SIZE * 3 / 4, SCREEN_SIZE / 2
        x_center = SCREEN_SIZE / 4, SCREEN_SIZE / 2
        if scene1:
            rect1 = pygame.draw.rect(screen, "black", (0, 0, SCREEN_SIZE / 2, SCREEN_SIZE))
            rect2 = pygame.draw.rect(screen, "black", (SCREEN_SIZE / 2, 0, SCREEN_SIZE / 2, SCREEN_SIZE))
            radius = 40

            mouse_pos = pygame.mouse.get_pos()
            if pygame.Rect.collidepoint(rect1, mouse_pos):
                pygame.draw.rect(screen, "dodgerblue4", (0, 0, SCREEN_SIZE / 2, SCREEN_SIZE))
                draw_x(screen, "white", x_center, radius, 20)
                pygame.draw.circle(screen, "white", circle_center, radius, 5)
            elif pygame.Rect.collidepoint(rect2, mouse_pos):
                pygame.draw.rect(screen, "firebrick3", (SCREEN_SIZE / 2, 0, SCREEN_SIZE / 2, SCREEN_SIZE))
                draw_x(screen, "white", x_center, radius, 5)
                pygame.draw.circle(screen, "white", circle_center, radius, 20)

            if cell_clicked_event is not None:
                if cell_clicked_event.pos[0] < SCREEN_SIZE / 2:
                    player_char = "x"
                    computer_char = "o"
                else:
                    player_char = "o"
                    computer_char = "x"
                    player_turn = False
                scene1 = False
                scene2 = True
        if scene2:
            box_width = 50
            box_height = 32
            box_gap = 40
            box_margin = 5
            center = (SCREEN_SIZE // 2, SCREEN_SIZE * 1 / 4)
            form_center = (SCREEN_SIZE // 2, SCREEN_SIZE // 2)

            if player_char == "x":
                pygame.draw.rect(screen, "dodgerblue4", (0, 0, SCREEN_SIZE, SCREEN_SIZE))
                draw_x(screen, "white", center, radius, 20)
            elif player_char == "o":
                pygame.draw.rect(screen, "firebrick3", (0, 0, SCREEN_SIZE, SCREEN_SIZE))
                pygame.draw.circle(screen, "white", center, radius, 20)

            bs = font.render("Board size (1-50):", True, "white")
            sir = font.render("Stones in row (1-10):", True, "white")
            screen.blit(bs, (form_center[0] - 6 * box_width, form_center[1] - box_height + box_margin))
            screen.blit(sir, (form_center[0] - 6 * box_width, form_center[1] - box_height + box_margin + box_gap))

            if not input_boxes: 
                input_boxes += [
                    InputBox(form_center[0] - box_width, form_center[1] - box_height, box_width, box_height,
                             color_active, color_inactive, font, "5"),
                    InputBox(form_center[0] - box_width, form_center[1] - box_height + box_gap, box_width, box_height,
                             color_active, color_inactive, font, "3")
                ]
            for box in input_boxes:
                box.draw(screen)
            
            if button is None:
                button = Button(form_center[0] - box_width, form_center[1] - box_height + 2 * box_gap, 80, 40, "black", "white", font, "Start")

            pygame.draw.rect(screen, button.color, button.rect)
            screen.blit(button.text, (button.rect.x + 15, button.rect.y + 10))
        if scene3:
            cell_size = SCREEN_SIZE // grid_size
            outer_border = (SCREEN_SIZE % grid_size) // 2
            for i, row in enumerate(field_cells):
                for j, cell in enumerate(row):
                    rect_left = j * cell_size + 1 + outer_border
                    rect_top = i * cell_size + 1 + outer_border
                    border = 2

                    pygame.draw.rect(screen, "white", (rect_left, rect_top, cell_size - border, cell_size - border))
                    if cell[1] in winning_indices:
                        pygame.draw.rect(screen, "green", (rect_left, rect_top, cell_size - border, cell_size - border))

                    center = (rect_left + ((cell_size - border) // 2) , rect_top + ((cell_size - border) // 2))
                    radius = cell_size // 3
                    thicc = cell_size // 10
                    if cell[0] == "x":
                        draw_x(screen, "blue", center, radius, thicc)
                    elif cell[0] == "o":
                        pygame.draw.circle(screen, "red", center, radius, thicc)
        
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