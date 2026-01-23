import pygame
import sys
import math
from pygame.locals import *
pygame.init()
WIDTH, HEIGHT = 1100, 800
BACKGROUND_COLOR = (10, 10, 20)
GRID_COLOR = (40, 40, 60)
POSITIVE_COLOR = (255, 50, 50)
NEGATIVE_COLOR = (50, 100, 255)
NEUTRAL_COLOR = (100, 200, 100)
FIELD_COLOR = (255, 255, 100)
FORCE_COLOR = (255, 150, 50)
TEXT_COLOR = (220, 220, 220)
GRID_SIZE = 50
k = 8.99e9
MIN_CHARGE = 0.1
MAX_CHARGE = 10.0
HEATMAP_MIN = 1
HEATMAP_MAX = 1e8
def format_scientific(value):
    if value == 0: return "0"
    exponent = int(math.floor(math.log10(abs(value))))
    mantissa = value / (10 ** exponent)
    mantissa = round(mantissa, 2)
    if exponent == 0: return f"{mantissa:.2f}"
    return f"{mantissa:.2f}×10^{exponent}"
def get_heatmap_color(value, min_val, max_val):
    if max_val - min_val < 1e-10: return (128, 0, 128)
    normalized = (value - min_val) / (max_val - min_val)
    normalized = max(0, min(1, normalized))
    if normalized < 0.25:
        blue = 255
        red = int(64 * normalized * 4)
        green = int(64 * normalized * 4)
    elif normalized < 0.5:
        blue = 255
        green = int(128 + 127 * (normalized - 0.25) * 4)
        red = int(64 + 64 * (normalized - 0.25) * 4)
    elif normalized < 0.75:
        green = 255
        red = int(128 + 127 * (normalized - 0.5) * 4)
        blue = int(255 - 255 * (normalized - 0.5) * 4)
    else:
        red = 255
        green = int(255 - 255 * (normalized - 0.75) * 4)
        blue = 0
    return (red, green, blue)
class Charge:
    def __init__(self, x, y, q=1.0, radius=20):
        self.x = x
        self.y = y
        self.q = q
        self.radius = radius
        self.dragging = False
        self.selected = False
    def draw(self, screen):
        if self.q > 0:
            color = POSITIVE_COLOR
            sign = "+"
        else:
            color = NEGATIVE_COLOR
            sign = "-"
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.radius)
        if self.selected:
            pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)),
                             self.radius + 2, 2)
        font = pygame.font.SysFont(None, 24)
        text = font.render(f"{sign}{abs(self.q):.1f}", True, TEXT_COLOR)
        text_rect = text.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(text, text_rect)
    def is_inside(self, x, y):
        distance = math.sqrt((x - self.x)**2 + (y - self.y)**2)
        return distance <= self.radius
    def move(self, x, y):
        self.x = x
        self.y = y
class FieldPoint:
    def __init__(self, x, y, show_vector=True):
        self.x = x
        self.y = y
        self.show_vector = show_vector
        self.radius = 8
        self.dragging = False
        self.selected = False
    def draw(self, screen):
        color = NEUTRAL_COLOR
        if self.selected:
            color = (255, 255, 255)
            pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.radius + 2, 2)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.radius)
    def is_inside(self, x, y):
        distance = math.sqrt((x - self.x)**2 + (y - self.y)**2)
        return distance <= self.radius
    def move(self, x, y):
        self.x = x
        self.y = y
class ElectricFieldSimulator:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Электрическое поле")
        self.clock = pygame.time.Clock()
        self.charges = []
        self.field_points = []
        self.selected_charge = None
        self.selected_field_point = None
        self.mode = "select"
        self.charge_sign = 1
        self.charge_value = 1.0
        self.show_vectors = True
        self.show_grid = True
        self.show_heatmap = False
        self.heatmap_surface = None
        self.heatmap_min = HEATMAP_MIN
        self.heatmap_max = HEATMAP_MAX
        self.last_heatmap_update_time = 0
        self.heatmap_update_interval = 10
        self.heatmap_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.update_heatmap()
    def update_heatmap(self):
        if not self.heatmap_surface: return
        self.heatmap_surface.fill((0, 0, 0, 0))
        cell_size = 10
        log_min = math.log10(HEATMAP_MIN)
        log_max = math.log10(HEATMAP_MAX)
        for y in range(0, HEIGHT, cell_size):
            for x in range(0, WIDTH, cell_size):
                Ex, Ey = self.calculate_electric_field(x + cell_size//2, y + cell_size//2)
                E_magnitude = math.sqrt(Ex**2 + Ey**2)
                log_E = math.log10(E_magnitude + 1e-10)
                normalized = (log_E - log_min) / (log_max - log_min)
                normalized = max(0, min(1, normalized))
                color = get_heatmap_color(normalized * 100, 0, 100)
                rect = pygame.Rect(x, y, cell_size, cell_size)
                pygame.draw.rect(self.heatmap_surface, (*color, 180), rect)
        self.last_heatmap_update_time = pygame.time.get_ticks()
    def calculate_electric_field(self, x, y):
        Ex, Ey = 0, 0
        for charge in self.charges:
            dx = x - charge.x
            dy = y - charge.y
            r_sq = dx**2 + dy**2
            if r_sq > 0:
                E_magnitude = k * abs(charge.q) / (r_sq + 100)
                if charge.q > 0:
                    Ex += E_magnitude * dx / math.sqrt(r_sq + 100)
                    Ey += E_magnitude * dy / math.sqrt(r_sq + 100)
                else:
                    Ex -= E_magnitude * dx / math.sqrt(r_sq + 100)
                    Ey -= E_magnitude * dy / math.sqrt(r_sq + 100)
        return Ex, Ey
    def calculate_force_on_charge(self, charge):
        Fx, Fy = 0, 0
        for other in self.charges:
            if other != charge:
                dx = other.x - charge.x
                dy = other.y - charge.y
                r_sq = dx**2 + dy**2
                if r_sq > 0:
                    force_magnitude = k * abs(charge.q * other.q) / r_sq
                    if charge.q * other.q > 0:
                        Fx -= force_magnitude * dx / math.sqrt(r_sq)
                        Fy -= force_magnitude * dy / math.sqrt(r_sq)
                    else:
                        Fx += force_magnitude * dx / math.sqrt(r_sq)
                        Fy += force_magnitude * dy / math.sqrt(r_sq)
        return Fx, Fy
    def draw_grid(self):
        if not self.show_grid: return
        for x in range(0, WIDTH, GRID_SIZE): pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT, GRID_SIZE): pygame.draw.line(self.screen, GRID_COLOR, (0, y), (WIDTH, y), 1)
    def draw_vectors(self):
        if not self.show_vectors: return
        for point in self.field_points:
            if point.show_vector:
                Ex, Ey = self.calculate_electric_field(point.x, point.y)
                E_magnitude = math.sqrt(Ex**2 + Ey**2)
                if E_magnitude > 0:
                    scale = min(200, 100 / (E_magnitude + 1e-10))
                    end_x = point.x + Ex * scale
                    end_y = point.y + Ey * scale
                    pygame.draw.line(self.screen, FIELD_COLOR,
                                   (int(point.x), int(point.y)),
                                   (int(end_x), int(end_y)), 3)
                    self.draw_arrow(point.x, point.y, end_x, end_y, FIELD_COLOR)
        for charge in self.charges:
            Fx, Fy = self.calculate_force_on_charge(charge)
            F_magnitude = math.sqrt(Fx**2 + Fy**2)
            if F_magnitude > 0:
                scale = min(200, 100 / (F_magnitude + 1e-10))
                end_x = charge.x + Fx * scale
                end_y = charge.y + Fy * scale
                pygame.draw.line(self.screen, FORCE_COLOR,
                               (int(charge.x), int(charge.y)),
                               (int(end_x), int(end_y)), 3)
                self.draw_arrow(charge.x, charge.y, end_x, end_y, FORCE_COLOR)
    def draw_arrow(self, start_x, start_y, end_x, end_y, color):
        angle = math.atan2(end_y - start_y, end_x - start_x)
        arrow_length = 15
        x1 = end_x - arrow_length * math.cos(angle - math.pi/6)
        y1 = end_y - arrow_length * math.sin(angle - math.pi/6)
        x2 = end_x - arrow_length * math.cos(angle + math.pi/6)
        y2 = end_y - arrow_length * math.sin(angle + math.pi/6)
        pygame.draw.polygon(self.screen, color,
                          [(end_x, end_y), (x1, y1), (x2, y2)])
    def draw_ui(self):
        panel_rect = pygame.Rect(10, 49, 280, 180)
        pygame.draw.rect(self.screen, (40, 40, 50), panel_rect)
        pygame.draw.rect(self.screen, (80, 80, 100), panel_rect, 2)
        small_font = pygame.font.SysFont(None, 22)
        instructions = [
            "ЛКМ - выбрать/перетащить",
            "E - добавить заряд +",
            "Q - добавить заряд -",
            "F - добавить точку поля",
            "Del - удалить выбранное",
            "Пробел - векторы",
            "G - сетка",
            "H - тепловая карта",
            "Колесико - изменить заряд"
        ]
        for i, text in enumerate(instructions):
            instruction = small_font.render(text, True, TEXT_COLOR)
            self.screen.blit(instruction, (20, 50 + i * 20))
        if self.selected_charge:
            info_rect = pygame.Rect(WIDTH - 280, 10, 270, 120)
            pygame.draw.rect(self.screen, (50, 50, 60), info_rect)
            pygame.draw.rect(self.screen, (100, 100, 120), info_rect, 2)
            charge = self.selected_charge
            Fx, Fy = self.calculate_force_on_charge(charge)
            force_magnitude = math.sqrt(Fx**2 + Fy**2)
            force_str = format_scientific(force_magnitude)
            info_lines = [
                f"Выбранный заряд:",
                f"Величина: {'+' if charge.q > 0 else '-'}{abs(charge.q):.2f}",
                f"Позиция: ({charge.x:.0f}, {charge.y:.0f})",
                f"Сила: {force_str} Н"
            ]
            for i, line in enumerate(info_lines):
                info_text = small_font.render(line, True, TEXT_COLOR)
                self.screen.blit(info_text, (WIDTH - 270, 20 + i * 20))
        if self.show_heatmap:
            legend_rect = pygame.Rect(WIDTH - 150, HEIGHT - 150, 130, 130)
            pygame.draw.rect(self.screen, (30, 30, 40), legend_rect)
            pygame.draw.rect(self.screen, (80, 80, 100), legend_rect, 2)
            legend_title = small_font.render("Напряженность", True, TEXT_COLOR)
            self.screen.blit(legend_title, (WIDTH - 145, HEIGHT - 145))
            for i in range(100):
                y_pos = HEIGHT - 120 + i
                normalized = i / 100
                color = get_heatmap_color(normalized * 100, 0, 100)
                pygame.draw.line(self.screen, color, (WIDTH - 140, y_pos), (WIDTH - 100, y_pos), 2)
            min_str = format_scientific(HEATMAP_MIN)
            max_str = format_scientific(HEATMAP_MAX)
            min_text = small_font.render(f"{min_str}", True, TEXT_COLOR)
            max_text = small_font.render(f"{max_str}", True, TEXT_COLOR)
            self.screen.blit(min_text, (WIDTH - 95, HEIGHT - 125))
            self.screen.blit(max_text, (WIDTH - 95, HEIGHT - 25))
            log_text = small_font.render("лог. шкала", True, TEXT_COLOR)
            self.screen.blit(log_text, (WIDTH - 140, HEIGHT - 155))
    def get_mode_text(self):
        modes = {
            "select": "Выбор",
            "add_field": "Точка поля"
        }
        return modes.get(self.mode, "Неизвестно")
    def check_periodic_heatmap_update(self):
        if not self.show_heatmap: return
        current_time = pygame.time.get_ticks()
        time_since_update = current_time - self.last_heatmap_update_time
        if time_since_update >= self.heatmap_update_interval: self.update_heatmap()
    def handle_events(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                if event.key == K_1: self.mode = "select"
                elif event.key == K_2: self.mode = "add_field"
                elif event.key == K_e:
                    new_charge = Charge(mouse_x, mouse_y, self.charge_value)
                    self.charges.append(new_charge)
                elif event.key == K_q:
                    new_charge = Charge(mouse_x, mouse_y, -self.charge_value)
                    self.charges.append(new_charge)
                elif event.key == K_f:
                    new_point = FieldPoint(mouse_x, mouse_y)
                    self.field_points.append(new_point)
                elif event.key == K_SPACE: self.show_vectors = not self.show_vectors
                elif event.key == K_g: self.show_grid = not self.show_grid
                elif event.key == K_h: self.show_heatmap = not self.show_heatmap
                elif event.key == K_DELETE:
                    if self.selected_charge:
                        self.charges.remove(self.selected_charge)
                        self.selected_charge = None
                    elif self.selected_field_point:
                        self.field_points.remove(self.selected_field_point)
                        self.selected_field_point = None
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    charge_clicked = False
                    for charge in self.charges:
                        if charge.is_inside(mouse_x, mouse_y):
                            if self.selected_charge: self.selected_charge.selected = False
                            if self.selected_field_point:
                                self.selected_field_point.selected = False
                                self.selected_field_point = None
                            charge.selected = True
                            self.selected_charge = charge
                            charge.dragging = True
                            charge_clicked = True
                            break
                    if not charge_clicked:
                        for point in self.field_points:
                            if point.is_inside(mouse_x, mouse_y):
                                if self.selected_charge:
                                    self.selected_charge.selected = False
                                    self.selected_charge = None
                                if self.selected_field_point: self.selected_field_point.selected = False
                                point.selected = True
                                self.selected_field_point = point
                                point.dragging = True
                                break
                elif event.button == 4:
                    if self.selected_charge:
                        self.selected_charge.q = min(
                            abs(self.selected_charge.q) + 0.5,
                            MAX_CHARGE
                        ) * (1 if self.selected_charge.q > 0 else -1)
                elif event.button == 5:
                    if self.selected_charge:
                        new_q = max(abs(self.selected_charge.q) - 0.5, MIN_CHARGE)
                        self.selected_charge.q = new_q * (1 if self.selected_charge.q > 0 else -1)
            elif event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    for charge in self.charges: charge.dragging = False
                    for point in self.field_points: point.dragging = False
            elif event.type == MOUSEMOTION:
                for charge in self.charges:
                    if charge.dragging: charge.move(mouse_x, mouse_y)
                for point in self.field_points:
                    if point.dragging: point.move(mouse_x, mouse_y)
    def run(self):
        running = True
        while running:
            self.handle_events()
            self.check_periodic_heatmap_update()
            self.screen.fill(BACKGROUND_COLOR)
            if self.show_heatmap: self.screen.blit(self.heatmap_surface, (0, 0))
            if self.show_grid: self.draw_grid()
            for point in self.field_points: point.draw(self.screen)
            for charge in self.charges: charge.draw(self.screen)
            if self.show_vectors: self.draw_vectors()
            self.draw_ui()
            pygame.display.flip()
            self.clock.tick(60)
if __name__ == "__main__":
    simulator = ElectricFieldSimulator()
    simulator.run()