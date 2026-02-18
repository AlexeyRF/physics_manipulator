import pygame
import math

WIDTH, HEIGHT = 1200, 800
FPS = 60
BG_COLOR = (20, 20, 25)
GRID_COLOR = (40, 40, 50)
TEXT_COLOR = (200, 200, 200)
RAY_COLOR = (255, 50, 50)
SHADOW_RAY_COLOR = (255, 255, 200, 20)
OBJ_COLOR = (255, 255, 255)
SELECT_COLOR = (0, 255, 0)
IMG_POINT_COLOR = (100, 100, 255)

TYPE_LAMP = 1
TYPE_WALL = 2
TYPE_LASER = 3
TYPE_MIRROR = 4
TYPE_LENS = 5
TYPE_BLOCK = 6

MAX_DEPTH = 10
AIR_REFRACTIVE_INDEX = 1.0

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Свагалятор: отптическая сцена")
font = pygame.font.SysFont('Arial', 16)
large_font = pygame.font.SysFont('Arial', 24)

def rotate_point(p, center, angle_deg):
    angle_rad = math.radians(angle_deg)
    x, y = p
    cx, cy = center
    nx = cx + (x - cx) * math.cos(angle_rad) - (y - cy) * math.sin(angle_rad)
    ny = cy + (x - cx) * math.sin(angle_rad) + (y - cy) * math.cos(angle_rad)
    return nx, ny

def normalize(v):
    l = math.hypot(v[0], v[1])
    if l == 0: return (0, 0)
    return (v[0]/l, v[1]/l)

def dot(v1, v2): return v1[0]*v2[0] + v1[1]*v2[1]

def reflect(direction, normal):
    d = dot(direction, normal)
    return (direction[0] - 2*d*normal[0], direction[1] - 2*d*normal[1])

def refract(direction, normal, n1, n2):
    d = dot(direction, normal)
    eta = n1 / n2
    k = 1 - eta**2 * (1 - d**2)
    if k < 0: return None
    return (eta * direction[0] - (eta * d + math.sqrt(k)) * normal[0], eta * direction[1] - (eta * d + math.sqrt(k)) * normal[1])

def intersect_line_segment(ray_origin, ray_dir, p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = ray_origin
    x4, y4 = (x3 + ray_dir[0], y3 + ray_dir[1])
    denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
    if denom == 0: return None
    ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom
    ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denom
    if 0 <= ua <= 1 and ub > 0.001:
        ix = x1 + ua * (x2 - x1)
        iy = y1 + ua * (y2 - y1)
        dist = ub
        return (ix, iy), dist
    return None

class OpticObject:
    def __init__(self, x, y, obj_type):
        self.x = x
        self.y = y
        self.type = obj_type
        self.angle = 0
        self.scale = 100
        self.param = 1.5
        if self.type == TYPE_LENS: self.param = 0.01
        if self.type == TYPE_BLOCK: self.param = 1.5

    def get_segments(self):
        w = self.scale / 2
        h = 5
        if self.type == TYPE_BLOCK or self.type == TYPE_WALL: h = self.scale / 2
        pts = [(-w, -h), (w, -h), (w, h), (-w, h)]
        rot_pts = [rotate_point((self.x + p[0], self.y + p[1]), (self.x, self.y), self.angle) for p in pts]
        segments = []
        for i in range(4):
            p1 = rot_pts[i]
            p2 = rot_pts[(i+1)%4]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            normal = normalize((-dy, dx))
            is_refr = (self.type == TYPE_BLOCK or self.type == TYPE_LENS)
            segments.append({'p1': p1, 'p2': p2, 'norm': normal, 'obj': self})
            if (self.type == TYPE_MIRROR or self.type == TYPE_LENS) and i == 0: return [segments[-1]]
        return segments

    def draw(self, surf, selected=False):
        color = SELECT_COLOR if selected else OBJ_COLOR
        if self.type in [TYPE_WALL, TYPE_BLOCK]:
            rect_pts = [s['p1'] for s in self.get_segments()]
            pygame.draw.polygon(surf, color if self.type == TYPE_WALL else (100, 200, 255), rect_pts, 2 if self.type==TYPE_BLOCK else 0)
            if self.type == TYPE_BLOCK:
                text = font.render(f"n={self.param:.2f}", True, TEXT_COLOR)
                surf.blit(text, (self.x - 20, self.y - 10))
        elif self.type in [TYPE_MIRROR, TYPE_LENS]:
            seg = self.get_segments()[0]
            p1, p2 = seg['p1'], seg['p2']
            pygame.draw.line(surf, color, p1, p2, 3)
            if self.type == TYPE_MIRROR:
                center = ((p1[0]+p2[0])/2, (p1[1]+p2[1])/2)
                norm = seg['norm']
                pygame.draw.line(surf, (100,100,100), center, (center[0]-norm[0]*10, center[1]-norm[1]*10), 1)
            elif self.type == TYPE_LENS:
                sign = 1 if self.param > 0 else -1
                pygame.draw.circle(surf, color, (int(p1[0]), int(p1[1])), 4)
                pygame.draw.circle(surf, (255,100,100) if sign<0 else (100,255,100), (int(p1[0]), int(p1[1])), 2)
                pygame.draw.circle(surf, color, (int(p2[0]), int(p2[1])), 4)
                t_txt = "Рассеивающая" if self.param > 0 else "Собирающая"
                text = font.render(f"{t_txt} П={self.param*1000:.1f}", True, TEXT_COLOR)
                surf.blit(text, (self.x + 10, self.y + 10))
        elif self.type in [TYPE_LAMP, TYPE_LASER]:
            pygame.draw.circle(surf, color, (int(self.x), int(self.y)), 10)
            label = "СВТ" if self.type == TYPE_LAMP else "ЛУЧ"
            surf.blit(font.render(label, True, (0,0,0)), (self.x-10, self.y-8))

def cast_ray(start_pos, direction, objects, depth=0, intensity=1.0):
    if depth > MAX_DEPTH or intensity < 0.05: return []
    closest_hit = None
    min_dist = float('inf')
    segments = []
    for obj in objects:
        if obj.type not in [TYPE_LAMP, TYPE_LASER]: segments.extend(obj.get_segments())
    for seg in segments:
        hit = intersect_line_segment(start_pos, direction, seg['p1'], seg['p2'])
        if hit:
            pos, dist = hit
            if dist < min_dist:
                min_dist = dist
                closest_hit = (pos, seg)
    path = [start_pos]
    if closest_hit:
        hit_pos, seg = closest_hit
        obj = seg['obj']
        path.append(hit_pos)
        next_dir = None
        current_n = AIR_REFRACTIVE_INDEX
        entering = dot(direction, seg['norm']) < 0
        normal = seg['norm'] if entering else (-seg['norm'][0], -seg['norm'][1])
        if obj.type == TYPE_MIRROR: next_dir = reflect(direction, normal)
        elif obj.type == TYPE_WALL: return [path]
        elif obj.type == TYPE_BLOCK:
            n1 = AIR_REFRACTIVE_INDEX if entering else obj.param
            n2 = obj.param if entering else AIR_REFRACTIVE_INDEX
            next_dir = refract(direction, normal, n1, n2)
            if next_dir is None: next_dir = reflect(direction, normal)
        elif obj.type == TYPE_LENS:
            cx, cy = obj.x, obj.y
            lx, ly = hit_pos
            dx, dy = seg['p2'][0] - seg['p1'][0], seg['p2'][1] - seg['p1'][1]
            l_len = math.hypot(dx, dy)
            if l_len == 0: l_len = 1
            lens_vec = (dx/l_len, dy/l_len)
            dist_from_center = (lx - cx)*lens_vec[0] + (ly - cy)*lens_vec[1]
            deflection_angle = dist_from_center * obj.param * 0.1
            curr_angle = math.atan2(direction[1], direction[0])
            new_angle = curr_angle + deflection_angle
            next_dir = (math.cos(new_angle), math.sin(new_angle))
        if next_dir:
            offset_pos = (hit_pos[0] + next_dir[0]*0.1, hit_pos[1] + next_dir[1]*0.1)
            child_paths = cast_ray(offset_pos, next_dir, objects, depth + 1, intensity * 0.9)
            if child_paths: path.extend(child_paths[0][1:])
            return [path]
    else:
        end_pt = (start_pos[0] + direction[0]*2000, start_pos[1] + direction[1]*2000)
        path.append(end_pt)
        return [path]
    return [path]

def main():
    clock = pygame.time.Clock()
    running = True
    objects = []
    selected_idx = -1
    current_tool = TYPE_LASER

    while running:
        screen.fill(BG_COLOR)
        for x in range(0, WIDTH, 50): pygame.draw.line(screen, GRID_COLOR, (x,0), (x,HEIGHT))
        for y in range(0, HEIGHT, 50): pygame.draw.line(screen, GRID_COLOR, (0,y), (WIDTH,y))

        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: current_tool = TYPE_LAMP
                if event.key == pygame.K_2: current_tool = TYPE_WALL
                if event.key == pygame.K_3: current_tool = TYPE_LASER
                if event.key == pygame.K_4: current_tool = TYPE_MIRROR
                if event.key == pygame.K_5: current_tool = TYPE_LENS
                if event.key == pygame.K_6: current_tool = TYPE_BLOCK
                if event.key == pygame.K_e:
                    objects.append(OpticObject(mx, my, current_tool))
                    selected_idx = len(objects) - 1
                if event.key == pygame.K_DELETE and selected_idx != -1:
                    objects.pop(selected_idx)
                    selected_idx = -1

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    min_d = 50
                    clicked = -1
                    for i, obj in enumerate(objects):
                        d = math.hypot(obj.x - mx, obj.y - my)
                        if d < min_d:
                            min_d = d
                            clicked = i
                    selected_idx = clicked
                if event.button == 4 and selected_idx != -1: objects[selected_idx].scale += 5
                if event.button == 5 and selected_idx != -1: objects[selected_idx].scale = max(10, objects[selected_idx].scale - 5)

        keys = pygame.key.get_pressed()
        if selected_idx != -1 and selected_idx < len(objects):
            sel_obj = objects[selected_idx]
            if pygame.mouse.get_pressed()[0]: sel_obj.x, sel_obj.y = mx, my
            if keys[pygame.K_a]: sel_obj.angle -= 2
            if keys[pygame.K_d]: sel_obj.angle += 2
            if keys[pygame.K_UP]:
                if sel_obj.type == TYPE_LENS:
                    sel_obj.param += 0.001
                    if sel_obj.param > 0.215: sel_obj.param = 0.215
                    if sel_obj.param < -0.215: sel_obj.param = -0.215
                else:
                    sel_obj.param += 0.01
            if keys[pygame.K_DOWN]:
                if sel_obj.type == TYPE_LENS:
                    sel_obj.param -= 0.001
                    if sel_obj.param > 0.215: sel_obj.param = 0.215
                    if sel_obj.param < -0.215: sel_obj.param = -0.215
                else:
                    sel_obj.param -= 0.01
            if sel_obj.type == TYPE_BLOCK: sel_obj.param = max(1.0, sel_obj.param)

        intersections_points = []
        for obj in objects:
            if obj.type == TYPE_LASER:
                rad_angle = math.radians(obj.angle)
                direction = (math.cos(rad_angle), math.sin(rad_angle))
                rays = cast_ray((obj.x, obj.y), direction, objects)
                for path in rays: 
                    if len(path) > 1: pygame.draw.lines(screen, RAY_COLOR, False, path, 2)
            elif obj.type == TYPE_LAMP:
                for angle in range(0, 360, 5):
                    rad = math.radians(angle)
                    direction = (math.cos(rad), math.sin(rad))
                    rays = cast_ray((obj.x, obj.y), direction, objects, intensity=0.5)
                    for path in rays:
                        if len(path) > 1:
                            surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                            pygame.draw.lines(surf, SHADOW_RAY_COLOR, False, path, 1)
                            screen.blit(surf, (0,0))

        for i, obj in enumerate(objects): obj.draw(screen, selected=(i == selected_idx))

        tool_names = {1:"Свет", 2:"Стена", 3:"Луч", 4:"Зеркало", 5:"Линза", 6:"Среда"}
        ui_txt = f"Инструмент: {tool_names.get(current_tool)} | ID текущего: {selected_idx}"
        if selected_idx != -1:
            o = objects[selected_idx]
            ui_txt += f" | Параметр: {o.param:.3f} | Угол: {o.angle:.1f}"
        screen.blit(large_font.render(ui_txt, True, TEXT_COLOR), (10, 10))
        screen.blit(font.render("E: Поставить | Del: Удалить | Зажать: Двигать | Колёсико: Размер | A/D: Вращать | Стрелки: Параметры", True, (150,150,150)), (10, 40))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__": main()