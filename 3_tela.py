import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
import matplotlib.animation as animation
import warnings
warnings.filterwarnings('ignore')
class ParameterSettings:
    def __init__(self):
        self.N = 3
        self.positions = np.array([
            [-1.0,  0.0],
            [ 1.0,  0.0],
            [ 0.0,  0.6],
        ], dtype=float)
        self.velocities = np.array([
            [ 0.0, -0.15],
            [ 0.0,  0.15],
            [ 0.2,  0.0],
        ], dtype=float)
        self.masses = np.array([1.0, 1.0, 0.5])
        self.colors = ['red', 'blue', 'green', 'purple', 'orange', 'brown', 'pink', 'gray']
        self.G = 1e-1
        self.dt = 0.02
        self.softening = 1e-2
        self.vector_scale = 0.5
        self.max_history = 1000
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
    print("НАСТРОЙКА ПАРАМЕТРОВ ГРАВИТАЦИОННОЙ СИМУЛЯЦИИ")
    print("=" * 60)
    settings = ParameterSettings()
    print("\n1. ОБЩИЕ ПАРАМЕТРЫ СИМУЛЯЦИИ:")
    print("-" * 40)
    use_default = get_yes_no("Использовать значения по умолчанию?", default=True)
    if not use_default:
        settings.G = get_input("Гравитационная постоянная (G)", default=settings.G)
        settings.dt = get_input("Шаг по времени (dt)", default=settings.dt)
        settings.softening = get_input("Смягчение (softening)", default=settings.softening)
        settings.vector_scale = get_input("Масштаб стрелок (vector_scale)", default=settings.vector_scale)
        settings.max_history = get_input("Длина истории траекторий", default=settings.max_history, type_func=int)
    print("\n2. НАСТРОЙКА ТЕЛ:")
    print("-" * 40)
    if not use_default:
        settings.N = get_input("Количество тел (N)", default=settings.N, type_func=int)
    configure_bodies = True
    if use_default and settings.N == 3:
        print("\nИспользуются стандартные параметры для 3 тел:")
        print("Тело 1: m=1.0, x=-1.0, y=0.0, vx=0.0, vy=-0.15")
        print("Тело 2: m=1.0, x=1.0, y=0.0, vx=0.0, vy=0.15")
        print("Тело 3: m=0.5, x=0.0, y=0.6, vx=0.2, vy=0.0")
        configure_bodies = get_yes_no("\nНастроить параметры тел вручную?", default=False)
    elif use_default and settings.N != 3:
        print(f"\nИспользуются стандартные параметры для {settings.N} тел")
        configure_bodies = get_yes_no("Настроить параметры тел вручную?", default=False)
    else:
        configure_bodies = get_yes_no("Настроить параметры каждого тела вручную?", default=False)
    if configure_bodies:
        settings.masses = np.zeros(settings.N)
        settings.positions = np.zeros((settings.N, 2))
        settings.velocities = np.zeros((settings.N, 2))
        for i in range(settings.N):
            print(f"\nТЕЛО {i+1}:")
            print("-" * 30)
            settings.masses[i] = get_input(f"  Масса тела {i+1}", default=1.0)
            print(f"  Начальные координаты тела {i+1}:")
            settings.positions[i][0] = get_input(f"    X координата", default=0.0)
            settings.positions[i][1] = get_input(f"    Y координата", default=0.0)
            print(f"  Начальные скорости тела {i+1}:")
            settings.velocities[i][0] = get_input(f"    Vx (скорость по X)", default=0.0)
            settings.velocities[i][1] = get_input(f"    Vy (скорость по Y)", default=0.0)
    else:
        if settings.N != len(settings.masses):
            settings.masses = np.ones(settings.N)
            settings.positions = np.zeros((settings.N, 2))
            settings.velocities = np.zeros((settings.N, 2))
            for i in range(settings.N):
                angle = 2 * np.pi * i / settings.N
                radius = 2.0
                settings.positions[i][0] = radius * np.cos(angle)
                settings.positions[i][1] = radius * np.sin(angle)
                tangent = np.array([-np.sin(angle), np.cos(angle)])
                settings.velocities[i] = 0.3 * tangent
    print("\n" + "=" * 60)
    print("ИТОГОВЫЕ ПАРАМЕТРЫ СИМУЛЯЦИИ:")
    print("-" * 60)
    print(f"Количество тел: {settings.N}")
    print(f"Гравитационная постоянная (G): {settings.G}")
    print(f"Шаг по времени (dt): {settings.dt}")
    print(f"Смягчение (softening): {settings.softening}")
    print(f"Максимальная длина истории: {settings.max_history}")
    print("\nПараметры тел:")
    for i in range(min(settings.N, 5)):
        print(f"  Тело {i+1}: m={settings.masses[i]:.2f}, "
              f"позиция=({settings.positions[i][0]:.2f}, {settings.positions[i][1]:.2f}), "
              f"скорость=({settings.velocities[i][0]:.2f}, {settings.velocities[i][1]:.2f})")
    if settings.N > 5:
        print(f"  ... и еще {settings.N - 5} тел")
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
        self.ax.set_title("Гравитационное взаимодействие N тел", fontsize=14)
        self.ax.set_xlabel("X", fontsize=12)
        self.ax.set_ylabel("Y", fontsize=12)
        self.lines = []
        self.points = []
        self.arrows = []
        self.texts = []
        self.force_texts = []
        for i in range(self.N):
            color = self.settings.colors[i % len(self.settings.colors)]
            line, = self.ax.plot([], [], color=color, alpha=0.7, linewidth=1.5)
            point, = self.ax.plot([], [], 'o', color=color, markersize=12,
                                 markeredgecolor='black', markeredgewidth=1)
            self.lines.append(line)
            self.points.append(point)
        self.info_text = self.ax.text(0.02, 0.98, '', transform=self.ax.transAxes,
                                      verticalalignment='top', fontsize=10,
                                      bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9))
        self.legend = self.ax.legend([], [], loc='upper left', fontsize=10)
        self.ax.grid(True, alpha=0.3, linestyle='--')
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
        force_info = []
        kinetic_energy = 0
        potential_energy = 0
        for i in range(self.N):
            color = self.settings.colors[i % len(self.settings.colors)]
            pos_i = self.pos[i]
            total_force = acc_current[i] * self.settings.masses[i]
            force_mag = np.linalg.norm(total_force)
            speed = np.linalg.norm(self.vel[i])
            kinetic_energy += 0.5 * self.settings.masses[i] * speed**2
            for j in range(i+1, self.N):
                r = self.pos[j] - pos_i
                dist = np.sqrt(np.dot(r, r) + self.settings.softening**2)
                potential_energy -= self.settings.G * self.settings.masses[i] * self.settings.masses[j] / dist
            if force_mag > 1e-10:
                arrow = self.draw_arrow(pos_i, total_force,
                                       scale=self.settings.vector_scale,
                                       color='red', alpha=0.8)
                self.arrows.append(arrow)
            text = self.ax.text(pos_i[0] + 0.15, pos_i[1] + 0.15,
                              f"m={self.settings.masses[i]:.2f}",
                              fontsize=9, color=color, fontweight='bold',
                              bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
            self.texts.append(text)
            force_text = self.ax.text(pos_i[0] - 0.3, pos_i[1] - 0.3,
                                    f"F={force_mag:.2e}",
                                    fontsize=8, color='darkred', alpha=0.8)
            self.force_texts.append(force_text)
            force_info.append(f"Тело {i+1}: F={force_mag:.2e}")
        total_energy = kinetic_energy + potential_energy
        info_text = (f"Время: {self.time_elapsed:.2f} с\n"
                    f"Кадр: {self.frame_count}\n"
                    f"Состояние: {'ПАУЗА' if self.settings.paused else 'ЗАПУЩЕНО'}")
        self.info_text.set_text(info_text)
        legend_labels = []
        for i in range(self.N):
            color = self.settings.colors[i % len(self.settings.colors)]
            legend_labels.append(f"Тело {i+1} (m={self.settings.masses[i]:.2f})")
        self.legend = self.ax.legend(self.lines, legend_labels, loc='upper left', fontsize=9)
        all_x = []
        all_y = []
        for i in range(self.N):
            if len(self.history_x[i]) > 0:
                all_x.extend(self.history_x[i])
                all_y.extend(self.history_y[i])
        if len(all_x) > 0 and len(all_y) > 0:
            x_min, x_max = min(all_x), max(all_x)
            y_min, y_max = min(all_y), max(all_y)
            x_range = x_max - x_min
            y_range = y_max - y_min
            if x_range < 0.1:
                x_range = 0.1
            if y_range < 0.1:
                y_range = 0.1
            x_margin = x_range * 0.2
            y_margin = y_range * 0.2
            self.ax.set_xlim(x_min - x_margin, x_max + x_margin)
            self.ax.set_ylim(y_min - y_margin, y_max + y_margin)
        return self.lines + self.points + self.arrows + self.texts + self.force_texts + [self.info_text, self.legend]
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
        print("Управление в окне анимации:")
        print("  - Кнопка 'Пауза': приостановить/возобновить симуляцию")
        print("  - Кнопка 'Сброс': сбросить симуляцию к начальным условиям")
        print("\nВ консоли можно отслеживать сообщения о состоянии симуляции")
        print("=" * 60)
        ani = animation.FuncAnimation(self.fig, self.animation_frame,
                                     interval=50, blit=False, cache_frame_data=False)
        plt.tight_layout()
        plt.show()
def main():
    print("\n" + "=" * 60)
    print("СИМУЛЯЦИЯ ГРАВИТАЦИОННОГО ВЗАИМОДЕЙСТВИЯ N ТЕЛ")
    print("=" * 60)
    print("Программа моделирует движение тел под действием гравитации")
    print("и отображает силы в реальном времени.")
    print("=" * 60)
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
