import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
import matplotlib.animation as animation
import warnings
warnings.filterwarnings('ignore')

class ParameterSettings:
    def __init__(self):
        self.N = 2
        # Положения: Земля в центре (0,0), Комета подлетает издалека
        self.positions = np.array([
            [0.0,  0.0],   # Земля
            [-4.0,  3.0],  # Комета
        ], dtype=float)
        # Скорости: Земля покоится, у кометы высокая скорость направленная к Земле
        self.velocities = np.array([
            [ 0.0,   0.0],  # Земля
            [ 0.35, -0.1],  # Комета
        ], dtype=float)
        self.masses = np.array([10.0, 0.01]) # Земля намного тяжелее кометы
        self.colors = ['royalblue', 'darkgray'] # Синяя Земля, серая комета
        self.G = 1e-1
        self.dt = 0.02
        self.softening = 1e-2
        self.vector_scale = 1.0
        self.max_history = 2000
        self.paused = False
        self.reset_requested = False

def get_input(prompt, default=None, type_func=float):
    if default is not None:
        prompt = f"{prompt} [по умолчанию: {default}]: "
    else:
        prompt = f"{prompt}: "
    while True:
        try:
            value = input(prompt).strip()
            if value == "" and default is not None:
                return default
            return type_func(value)
        except ValueError:
            print(f"Ошибка: введите корректное значение типа {type_func.__name__}")

def get_yes_no(prompt, default=True):
    default_str = "Y/n" if default else "y/N"
    while True:
        answer = input(f"{prompt} [{default_str}]: ").strip().lower()
        if answer == "":
            return default
        if answer in ["y", "yes", "да", "д"]:
            return True
        if answer in ["n", "no", "нет", "н"]:
            return False
        print("Ошибка: введите 'y' или 'n'")

def configure_parameters_via_console():
    print("=" * 60)
    print("НАСТРОЙКА ПАРАМЕТРОВ СИМУЛЯЦИИ: ЗЕМЛЯ И КОМЕТА")
    print("=" * 60)
    settings = ParameterSettings()
    
    print("\n1. ОБЩИЕ ПАРАМЕТРЫ СИМУЛЯЦИИ:")
    print("-" * 40)
    use_default = get_yes_no("Использовать значения по умолчанию?", default=True)
    if not use_default:
        settings.G = get_input("Гравитационная постоянная (G)", default=settings.G)
        settings.dt = get_input("Шаг по времени (dt)", default=settings.dt)
        settings.softening = get_input("Смягчение (softening)", default=settings.softening)
        settings.vector_scale = get_input("Масштаб стрелок сил", default=settings.vector_scale)
        settings.max_history = get_input("Длина истории траекторий", default=settings.max_history, type_func=int)
    
    print("\n2. НАСТРОЙКА ТЕЛ:")
    print("-" * 40)
    configure_bodies = False
    if use_default:
        print("\nИспользуются стандартные космические параметры:")
        print("Земля (Тело 1): m=10.0, x=0.0,  y=0.0, vx=0.0,  vy=0.0")
        print("Комета (Тело 2): m=0.01, x=-4.0, y=3.0, vx=0.35, vy=-0.1")
        configure_bodies = get_yes_no("\nНастроить параметры тел вручную?", default=False)
    else:
        configure_bodies = get_yes_no("Настроить параметры Земли и кометы вручную?", default=False)
        
    if configure_bodies:
        for i in range(settings.N):
            name = "ЗЕМЛЯ (Тело 1)" if i == 0 else "КОМЕТА (Тело 2)"
            print(f"\n{name}:")
            print("-" * 30)
            settings.masses[i] = get_input(f"  Масса", default=settings.masses[i])
            print(f"  Начальные координаты:")
            settings.positions[i][0] = get_input(f"    X координата", default=settings.positions[i][0])
            settings.positions[i][1] = get_input(f"    Y координата", default=settings.positions[i][1])
            print(f"  Начальные скорости:")
            settings.velocities[i][0] = get_input(f"    Vx (скорость по X)", default=settings.velocities[i][0])
            settings.velocities[i][1] = get_input(f"    Vy (скорость по Y)", default=settings.velocities[i][1])
            
    print("\n" + "=" * 60)
    print("ИТОГОВЫЕ ПАРАМЕТРЫ СИМУЛЯЦИИ:")
    print("-" * 60)
    print(f"Гравитационная постоянная (G): {settings.G}")
    print(f"Шаг по времени (dt): {settings.dt}")
    print(f"Земля:  m={settings.masses[0]:.2f}, Позиция=({settings.positions[0][0]:.2f}, {settings.positions[0][1]:.2f})")
    print(f"Комета: m={settings.masses[1]:.4f}, Позиция=({settings.positions[1][0]:.2f}, {settings.positions[1][1]:.2f})")
    print("\n" + "=" * 60)
    return settings

class GravitySimulation:
    def __init__(self, settings):
        self.settings = settings
        self.N = settings.N
        self.pos = settings.positions.copy()
        self.vel = settings.velocities.copy()
        self.acc = self.compute_accelerations(self.pos)
        self.history_x = [[] for _ in range(self.N)]
        self.history_y = [[] for _ in range(self.N)]
        self.time_elapsed = 0.0
        self.frame_count = 0
        
        self.fig, self.ax = plt.subplots(figsize=(12, 10))
        self.ax.set_aspect("equal")
        self.ax.set_title("Движение кометы относительно Земли", fontsize=14)
        self.ax.set_xlabel("X", fontsize=12)
        self.ax.set_ylabel("Y", fontsize=12)
        
        self.lines = []
        self.points = []
        self.arrows = []
        self.texts = []
        self.force_texts = []
        
        # Настройка отображения (Земля больше, комета меньше)
        sizes = [16, 8] 
        for i in range(self.N):
            color = self.settings.colors[i % len(self.settings.colors)]
            line, = self.ax.plot([], [], color=color, alpha=0.6, linewidth=1.5)
            point, = self.ax.plot([], [], 'o', color=color, markersize=sizes[i],
                                 markeredgecolor='black', markeredgewidth=1)
            self.lines.append(line)
            self.points.append(point)
            
        self.info_text = self.ax.text(0.02, 0.98, '', transform=self.ax.transAxes,
                                      verticalalignment='top', fontsize=10,
                                      bbox=dict(boxstyle='round', facecolor='lightcyan', alpha=0.9))
        self.ax.grid(True, alpha=0.2, linestyle='--')
        self.create_buttons()

    def compute_accelerations(self, pos):
        acc = np.zeros_like(pos)
        for i in range(self.N):
            for j in range(self.N):
                if i == j:
                    continue
                r = pos[j] - pos[i]
                dist2 = np.dot(r, r) + self.settings.softening**2
                acc[i] += self.settings.G * self.settings.masses[j] * r / (dist2 ** 1.5)
        return acc

    def draw_arrow(self, start, vec, scale=1.0, color="black", alpha=1.0):
        end = start + vec * scale
        arrow = FancyArrowPatch(start, end, arrowstyle="->", color=color,
                               alpha=alpha, linewidth=1.5, zorder=5)
        self.ax.add_patch(arrow)
        return arrow

    def create_buttons(self):
        from matplotlib.widgets import Button
        ax_pause = plt.axes([0.81, 0.02, 0.1, 0.05])
        ax_reset = plt.axes([0.70, 0.02, 0.1, 0.05])
        self.btn_pause = Button(ax_pause, 'Пауза')
        self.btn_reset = Button(ax_reset, 'Сброс')
        self.btn_pause.on_clicked(self.toggle_pause)
        self.btn_reset.on_clicked(self.reset_simulation)

    def toggle_pause(self, event):
        self.settings.paused = not self.settings.paused
        print(f"\nСимуляция {'приостановлена' if self.settings.paused else 'возобновлена'}")

    def reset_simulation(self, event):
        self.settings.reset_requested = True
        print("\nСимуляция будет сброшена к начальным условиям")

    def update_simulation(self):
        if self.settings.paused:
            return
            
        # Интегратор Верле
        self.pos = self.pos + self.vel * self.settings.dt + 0.5 * self.acc * self.settings.dt**2
        new_acc = self.compute_accelerations(self.pos)
        self.vel = self.vel + 0.5 * (self.acc + new_acc) * self.settings.dt
        self.acc = new_acc
        
        for i in range(self.N):
            self.history_x[i].append(self.pos[i, 0])
            self.history_y[i].append(self.pos[i, 1])
            if len(self.history_x[i]) > self.settings.max_history:
                self.history_x[i] = self.history_x[i][-self.settings.max_history:]
                self.history_y[i] = self.history_y[i][-self.settings.max_history:]
                
        self.time_elapsed += self.settings.dt
        self.frame_count += 1
        
        # --- ВЫВОД СКОРОСТИ И УСКОРЕНИЯ КОМЕТЫ В КОНСОЛЬ ---
        comet_speed = np.linalg.norm(self.vel[1])
        comet_acc = np.linalg.norm(self.acc[1])
        print(f"[Время: {self.time_elapsed:6.2f}s] Комета -> Скорость: {comet_speed:6.4f} | Ускорение: {comet_acc:6.4f}", end='\r')

    def update_visualization(self):
        for arrow in self.arrows:
            arrow.remove()
        self.arrows.clear()
        for text in self.texts:
            text.remove()
        self.texts.clear()
        for force_text in self.force_texts:
            force_text.remove()
        self.force_texts.clear()
        
        for i in range(self.N):
            if len(self.history_x[i]) > 1:
                self.lines[i].set_data(self.history_x[i], self.history_y[i])
                
        for i in range(self.N):
            self.points[i].set_data([self.pos[i, 0]], [self.pos[i, 1]])
            
        acc_current = self.compute_accelerations(self.pos)
        
        for i in range(self.N):
            pos_i = self.pos[i]
            total_force = acc_current[i] * self.settings.masses[i]
            force_mag = np.linalg.norm(total_force)
            
            # Стрелка силы только для Кометы (на Землю действует малая сила отдачи)
            if i == 1 and force_mag > 1e-5:
                arrow = self.draw_arrow(pos_i, total_force,
                                       scale=self.settings.vector_scale * 10, # Увеличен масштаб для наглядности
                                       color='red', alpha=0.8)
                self.arrows.append(arrow)
                
            labels = ["Земля", "Комета"]
            text = self.ax.text(pos_i[0] + 0.15, pos_i[1] + 0.15,
                              labels[i],
                              fontsize=9, color=self.settings.colors[i], fontweight='bold',
                              bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
            self.texts.append(text)
            
        info_text = (f"Время: {self.time_elapsed:.2f} с\n"
                    f"Кадр: {self.frame_count}\n"
                    f"Скорость кометы: {np.linalg.norm(self.vel[1]):.3f}\n"
                    f"Состояние: {'ПАУЗА' if self.settings.paused else 'ЗАПУЩЕНО'}")
        self.info_text.set_text(info_text)
        
        # Фиксация осей, чтобы камера не «прыгала» слишком резко
        all_x = []
        all_y = []
        for i in range(self.N):
            if len(self.history_x[i]) > 0:
                all_x.extend(self.history_x[i])
                all_y.extend(self.history_y[i])
        if len(all_x) > 0 and len(all_y) > 0:
            x_min, x_max = min(all_x), max(all_x)
            y_min, y_max = min(all_y), max(all_y)
            x_range = max(x_max - x_min, 8.0)
            y_range = max(y_max - y_min, 8.0)
            
            x_margin = x_range * 0.2
            y_margin = y_range * 0.2
            self.ax.set_xlim(x_min - x_margin, x_max + x_margin)
            self.ax.set_ylim(y_min - y_margin, y_max + y_margin)
            
        return self.lines + self.points + self.arrows + self.texts + self.force_texts + [self.info_text]

    def animation_frame(self, frame_num):
        if self.settings.reset_requested:
            print(f"\nСброс симуляции к начальным условиям...")
            self.pos = self.settings.positions.copy()
            self.vel = self.settings.velocities.copy()
            self.acc = self.compute_accelerations(self.pos)
            self.history_x = [[] for _ in range(self.N)]
            self.history_y = [[] for _ in range(self.N)]
            self.time_elapsed = 0.0
            self.frame_count = 0
            self.settings.reset_requested = False
            
        self.update_simulation()
        return self.update_visualization()

    def run(self):
        print("\n" + "=" * 60)
        print("ЗАПУСК СИМУЛЯЦИИ")
        print("=" * 60)
        ani = animation.FuncAnimation(self.fig, self.animation_frame,
                                     interval=30, blit=False, cache_frame_data=False)
        plt.tight_layout()
        plt.show()

def main():
    settings = configure_parameters_via_console()
    sim = GravitySimulation(settings)
    sim.run()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nПрограмма завершена пользователем.")
    except Exception as e:
        print(f"\nПроизошла ошибка: {e}")
        print("Программа завершена.")