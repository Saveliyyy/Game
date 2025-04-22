import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from PIL import Image, ImageTk
import random
from enum import Enum
import threading
import time


# ========== БАЗОВЫЕ КЛАССЫ ==========
class StatusEffect(Enum):
    POISONED = "Отравление"
    BURNING = "Горение"
    FROZEN = "Заморозка"
    BLESSED = "Благословение"


class SpellType(Enum):
    FIREBALL = "Огненный шар"
    ICE_SHACKLES = "Оковы льда"
    HEAL = "Исцеление"
    LIGHTNING = "Молния"


class ArtifactType(Enum):
    WEAPON = "Оружие"
    ARMOR = "Броня"
    POTION = "Зелье"
    SCROLL = "Свиток"
    RING = "Кольцо"
    AMULET = "Амулет"


class Artifact:
    def __init__(self, name, artifact_type, power):
        self.name = name
        self.type = artifact_type
        self.power = power

    def __str__(self):
        return f"{self.type.value}: {self.name} (+{self.power})"


class Location:
    def __init__(self, name, danger_level):
        self.name = name
        self.danger_level = danger_level
        self.artifacts = []
        self.generate_artifacts()

    def generate_artifacts(self):
        artifact_count = random.randint(0, 3)
        for _ in range(artifact_count):
            artifact_type = random.choice(list(ArtifactType))
            power = random.randint(1, 10) * self.danger_level

            if artifact_type == ArtifactType.WEAPON:
                name = random.choice(["Меч", "Топор", "Кинжал", "Посох", "Лук"])
            elif artifact_type == ArtifactType.ARMOR:
                name = random.choice(["Доспех", "Щит", "Шлем", "Перчатки", "Сапоги"])
            elif artifact_type == ArtifactType.POTION:
                name = random.choice(["Зелье здоровья", "Зелье маны", "Яд", "Эликсир"])
            elif artifact_type == ArtifactType.SCROLL:
                name = random.choice(["Свиток огня", "Свиток льда", "Свиток молнии"])
            elif artifact_type == ArtifactType.RING:
                name = random.choice(["Кольцо силы", "Кольцо защиты", "Кольцо магии"])
            else:
                name = random.choice(["Амулет здоровья", "Амулет маны", "Амулет защиты"])

            self.artifacts.append(Artifact(name, artifact_type, power))

    def get_artifact(self):
        if self.artifacts:
            return self.artifacts.pop()
        return None


# ========== КЛАССЫ ПЕРСОНАЖЕЙ ==========
class NPC:
    def __init__(self, name):
        self.name = name
        self.health = 100
        self.max_health = 100
        self.level = 1
        self.experience = 0
        self.inventory = []
        self.status_effects = {}
        self.is_alive = True
        self.current_location = None
        self.equipment = {
            "weapon": None,
            "armor": None,
            "ring": None,
            "amulet": None
        }
        self.gold = random.randint(0, 50)
        self.state = "exploring"  # exploring, fighting, resting, dead
        self.target = None

    def join_party(self):
        return f"К партии присоединяется {self.name}"

    def gain_exp(self, amount):
        self.experience += amount
        if self.experience >= 100 * self.level:
            return self.level_up()
        return f"{self.name} получает {amount} опыта."

    def level_up(self):
        self.level += 1
        self.max_health += 20
        self.health = self.max_health
        self.experience = 0
        return f"{self.name} достигает {self.level} уровня!"

    def add_status(self, effect: StatusEffect, duration: int):
        self.status_effects[effect] = duration
        return f"{self.name} получает эффект '{effect.value}' ({duration} ходов)"

    def update_statuses(self):
        results = []
        for effect in list(self.status_effects.keys()):
            self.status_effects[effect] -= 1
            if self.status_effects[effect] <= 0:
                del self.status_effects[effect]
                results.append(f"Эффект '{effect.value}' на {self.name} рассеивается")

            if effect == StatusEffect.POISONED:
                self.take_damage(5)
                results.append(f"{self.name} страдает от отравления")

            elif effect == StatusEffect.BURNING:
                self.take_damage(10)
                results.append(f"{self.name} горит!")

        return results

    def take_damage(self, damage):
        # Учитываем защиту от брони
        armor_defense = self.equipment["armor"].power if self.equipment["armor"] else 0
        actual_damage = max(1, damage - armor_defense // 2)

        self.health = max(0, self.health - actual_damage)
        if self.health == 0:
            self.die()
            return f"{self.name} повержен!"
        return f"{self.name} теряет {actual_damage} здоровья. Осталось: {self.health} HP"

    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)
        return f"{self.name} восстанавливает {amount} здоровья."

    def attack(self, target):
        """Базовый метод атаки"""
        # Учитываем силу оружия
        weapon_power = self.equipment["weapon"].power if self.equipment["weapon"] else 0
        damage = random.randint(5 + weapon_power, 10 + weapon_power * 2)
        target.take_damage(damage)
        return f"{self.name} атакует {target.name} и наносит {damage} урона!"

    def die(self):
        self.is_alive = False
        self.state = "dead"
        return f"{self.name} умирает!"

    def explore(self, world):
        if not self.is_alive:
            return []

        events = []
        # Выбираем случайную локацию
        self.current_location = random.choice(world.locations)
        events.append(f"{self.name} исследует {self.current_location.name}")

        # Поиск артефактов
        artifact = self.current_location.get_artifact()
        if artifact:
            self.inventory.append(artifact)
            events.append(f"{self.name} находит {artifact}!")

        # Шанс встретить другого NPC
        if random.random() < self.current_location.danger_level * 0.2:
            other_npcs = [npc for npc in world.npcs if npc != self and npc.is_alive]
            if other_npcs:
                target = random.choice(other_npcs)
                self.state = "fighting"
                self.target = target
                events.append(f"{self.name} встречает {target.name} и готовится к бою!")

        # Шанс найти золото
        if random.random() < 0.3:
            gold_found = random.randint(1, 20) * self.current_location.danger_level
            self.gold += gold_found
            events.append(f"{self.name} находит {gold_found} золота!")

        return events

    def fight(self, world):
        if not self.is_alive or not self.target or not self.target.is_alive:
            self.state = "exploring"
            self.target = None
            return []

        events = []

        # Атака цели
        if isinstance(self, Mage) and random.random() < 0.7:
            spell = random.choice(self.known_spells)
            events.append(self.cast_spell(spell, self.target))
        else:
            events.append(self.attack(self.target))

        # Проверка статусов
        status_events = self.target.update_statuses()
        events.extend(status_events)

        # Если цель мертва
        if not self.target.is_alive:
            events.append(f"{self.name} побеждает {self.target.name}!")
            exp_gain = random.randint(10, 30)
            events.append(self.gain_exp(exp_gain))
            self.gold += self.target.gold // 2
            events.append(f"{self.name} забирает {self.target.gold // 2} золота у {self.target.name}")
            self.state = "exploring"
            self.target = None

        # Ответный удар
        elif random.random() < 0.8:
            if isinstance(self.target, Mage) and random.random() < 0.7:
                spell = random.choice(self.target.known_spells)
                events.append(self.target.cast_spell(spell, self))
            else:
                events.append(self.target.attack(self))

            # Проверка статусов
            status_events = self.update_statuses()
            events.extend(status_events)

            if not self.is_alive:
                events.append(f"{self.name} был убит {self.target.name}!")
                self.target.gain_exp(random.randint(15, 25))
                self.target.gold += self.gold // 2
                events.append(f"{self.target.name} забирает {self.gold // 2} золота у {self.name}")

        return events

    def rest(self):
        if not self.is_alive:
            return []

        events = []
        heal_amount = random.randint(5, 15)
        events.append(self.heal(heal_amount))

        # Использование зелий
        potions = [item for item in self.inventory if item.type == ArtifactType.POTION]
        if potions and self.health < self.max_health * 0.5:
            potion = random.choice(potions)
            self.inventory.remove(potion)
            heal_amount = potion.power * 5
            events.append(f"{self.name} использует {potion.name}!")
            events.append(self.heal(heal_amount))

        # Случайное событие во время отдыха
        if random.random() < 0.2:
            events.append(f"{self.name} размышляет о жизни...")

        # Возвращение к исследованию
        if self.health > self.max_health * 0.7 or random.random() < 0.5:
            self.state = "exploring"
            events.append(f"{self.name} возобновляет исследование.")

        return events

    def update(self, world):
        if not self.is_alive:
            return []

        events = []

        # Выбор действия в зависимости от состояния
        if self.state == "exploring":
            events.extend(self.explore(world))
        elif self.state == "fighting":
            events.extend(self.fight(world))
        elif self.state == "resting":
            events.extend(self.rest())

        # Проверка необходимости отдыха
        if self.health < self.max_health * 0.4 and self.state != "fighting":
            self.state = "resting"
            events.append(f"{self.name} решает отдохнуть.")

        # Случайная смена состояния
        if random.random() < 0.1:
            if self.state == "exploring":
                self.state = "resting"
                events.append(f"{self.name} решает сделать перерыв.")
            elif self.state == "resting":
                self.state = "exploring"
                events.append(f"{self.name} решает продолжить исследование.")

        return events

    def equip_artifact(self, artifact):
        if artifact.type == ArtifactType.WEAPON:
            slot = "weapon"
        elif artifact.type == ArtifactType.ARMOR:
            slot = "armor"
        elif artifact.type == ArtifactType.RING:
            slot = "ring"
        elif artifact.type == ArtifactType.AMULET:
            slot = "amulet"
        else:
            return f"{artifact.name} нельзя экипировать"

        old_item = self.equipment[slot]
        if old_item:
            self.inventory.append(old_item)

        self.equipment[slot] = artifact
        self.inventory.remove(artifact)
        return f"{self.name} экипирует {artifact.name}"


class Mage(NPC):
    def __init__(self, name):
        super().__init__(name)
        self.mana = 150
        self.max_mana = 150
        self.known_spells = [SpellType.ICE_SHACKLES, SpellType.FIREBALL, SpellType.LIGHTNING]

    def cast_spell(self, spell: SpellType, target=None):
        if spell not in self.known_spells:
            return f"{self.name} не знает это заклинание"

        if self.mana < 20:
            return "Недостаточно маны"

        self.mana -= 20
        message = f"{self.name} кастует {spell.value}"

        if spell == SpellType.FIREBALL and target:
            target.take_damage(25)
            target.add_status(StatusEffect.BURNING, 3)
            message += f". {target.name} получает 25 урона!"

        elif spell == SpellType.ICE_SHACKLES and target:
            target.add_status(StatusEffect.FROZEN, 2)
            message += f". {target.name} заморожен!"

        elif spell == SpellType.LIGHTNING and target:
            target.take_damage(30)
            message += f". {target.name} получает 30 урона от молнии!"

        return message

    def rest(self):
        events = super().rest()
        # Восстановление маны во время отдыха
        mana_regen = random.randint(10, 25)
        self.mana = min(self.max_mana, self.mana + mana_regen)
        events.append(f"{self.name} восстанавливает {mana_regen} маны.")
        return events


class Warrior(NPC):
    def __init__(self, name):
        super().__init__(name)
        self.max_health = 150
        self.health = 150

    def attack(self, target):
        weapon_power = self.equipment["weapon"].power if self.equipment["weapon"] else 0
        damage = random.randint(15 + weapon_power, 25 + weapon_power * 2)
        target.take_damage(damage)
        return f"{self.name} мощно атакует {target.name} и наносит {damage} урона!"


class Rogue(NPC):
    def __init__(self, name):
        super().__init__(name)
        self.stealth = True

    def attack(self, target):
        weapon_power = self.equipment["weapon"].power if self.equipment["weapon"] else 0

        if self.stealth:
            damage = random.randint(20 + weapon_power * 2, 35 + weapon_power * 2)
            self.stealth = False
            return f"{self.name} бьёт в спину и наносит {damage} урона!"
        else:
            damage = random.randint(10 + weapon_power, 15 + weapon_power)
            self.stealth = random.choice([True, False])  # 50% шанс скрыться
            return f"{self.name} атакует {target.name} и наносит {damage} урона!"


# ========== СИСТЕМА МИРА ==========
class GameWorld:
    def __init__(self):
        self.npcs = []
        self.locations = [
            Location("Лес", 1),
            Location("Пещеры", 2),
            Location("Горы", 3),
            Location("Подземелье", 4),
            Location("Заброшенный город", 3),
            Location("Болото", 2),
            Location("Пустыня", 1)
        ]
        self.event_log = []
        self.is_running = False
        self.simulation_speed = 1.0

    def add_npc(self, npc):
        self.npcs.append(npc)
        self.log_event(npc.join_party())

    def log_event(self, event):
        self.event_log.append(event)
        # Ограничиваем размер лога
        if len(self.event_log) > 1000:
            self.event_log = self.event_log[-1000:]

    def simulate_turn(self):
        if not self.is_running:
            return

        # Обновляем всех NPC
        for npc in self.npcs:
            if npc.is_alive:
                events = npc.update(self)
                for event in events:
                    self.log_event(event)

        # Удаляем мертвых NPC
        dead_npcs = [npc for npc in self.npcs if not npc.is_alive]
        for npc in dead_npcs:
            self.npcs.remove(npc)
            self.log_event(f"Тело {npc.name} исчезает из мира...")

        # Случайные мировые события
        if random.random() < 0.1:
            event = random.choice([
                "Над миром проносится странный ветер...",
                "Где-то вдалеке слышен странный шум",
                "Небо на мгновение становится красным",
                "Земля слегка дрожит под ногами"
            ])
            self.log_event(event)

    def start_simulation(self):
        self.is_running = True
        self.log_event("=== СИМУЛЯЦИЯ НАЧИНАЕТСЯ ===")

    def stop_simulation(self):
        self.is_running = False
        self.log_event("=== СИМУЛЯЦИЯ ОСТАНОВЛЕНА ===")


# ========== ГРАФИЧЕСКИЙ ИНТЕРФЕЙС ==========
class GameGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RPG World Simulator")
        self.game_world = GameWorld()
        self.simulation_thread = None

        # Создание интерфейса
        self.create_widgets()
        self.update_ui()

    def create_widgets(self):
        # Панель управления
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        self.add_btn = ttk.Button(control_frame, text="Добавить персонажа", command=self.add_character)
        self.add_btn.pack(side=tk.LEFT, padx=2)

        self.start_btn = ttk.Button(control_frame, text="Старт", command=self.start_simulation)
        self.start_btn.pack(side=tk.LEFT, padx=2)

        self.stop_btn = ttk.Button(control_frame, text="Стоп", command=self.stop_simulation)
        self.stop_btn.pack(side=tk.LEFT, padx=2)

        # Скорость симуляции
        ttk.Label(control_frame, text="Скорость:").pack(side=tk.LEFT, padx=2)
        self.speed_var = tk.DoubleVar(value=1.0)
        self.speed_scale = ttk.Scale(control_frame, from_=0.1, to=5.0, variable=self.speed_var,
                                     command=lambda e: self.update_simulation_speed())
        self.speed_scale.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        # Лог событий
        log_frame = ttk.LabelFrame(self.root, text="Лог событий")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, width=80, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Статистика
        stats_frame = ttk.LabelFrame(self.root, text="Статистика")
        stats_frame.pack(fill=tk.BOTH, padx=5, pady=5)

        self.stats_text = tk.Text(stats_frame, width=80, height=10)
        self.stats_text.pack(fill=tk.BOTH)

    def update_simulation_speed(self):
        self.game_world.simulation_speed = self.speed_var.get()

    def add_character(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Создание персонажа")

        ttk.Label(dialog, text="Имя:").grid(row=0, column=0, padx=5, pady=5)
        name_entry = ttk.Entry(dialog)
        name_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(dialog, text="Класс:").grid(row=1, column=0, padx=5, pady=5)
        class_var = tk.StringVar()
        class_combo = ttk.Combobox(dialog, textvariable=class_var,
                                   values=["Маг", "Воин", "Разбойник"])
        class_combo.grid(row=1, column=1, padx=5, pady=5)
        class_combo.current(0)

        def create():
            name = name_entry.get()
            if not name:
                messagebox.showerror("Ошибка", "Введите имя персонажа")
                return

            if class_var.get() == "Маг":
                char = Mage(name)
            elif class_var.get() == "Воин":
                char = Warrior(name)
            else:
                char = Rogue(name)

            self.game_world.add_npc(char)
            self.update_ui()
            dialog.destroy()

        ttk.Button(dialog, text="Создать", command=create).grid(row=2, column=0, columnspan=2, pady=5)

    def start_simulation(self):
        if not self.game_world.npcs:
            messagebox.showwarning("Предупреждение", "Добавьте хотя бы одного персонажа")
            return

        if not self.game_world.is_running:
            self.game_world.start_simulation()
            self.simulation_thread = threading.Thread(target=self.run_simulation, daemon=True)
            self.simulation_thread.start()
            self.update_ui()

    def stop_simulation(self):
        if self.game_world.is_running:
            self.game_world.stop_simulation()
            self.update_ui()

    def run_simulation(self):
        while self.game_world.is_running:
            self.game_world.simulate_turn()
            self.root.after(100, self.update_ui)
            time.sleep(1.0 / self.game_world.simulation_speed)

    def update_ui(self):
        # Обновление лога событий
        self.log_text.delete(1.0, tk.END)
        for event in self.game_world.event_log[-100:]:  # Показываем последние 100 событий
            self.log_text.insert(tk.END, event + "\n")
        self.log_text.see(tk.END)

        # Обновление статистики
        self.stats_text.delete(1.0, tk.END)
        alive_npcs = [npc for npc in self.game_world.npcs if npc.is_alive]
        dead_npcs = [npc for npc in self.game_world.npcs if not npc.is_alive]

        self.stats_text.insert(tk.END, f"=== ЖИВЫЕ ПЕРСОНАЖИ ({len(alive_npcs)}) ===\n")
        for npc in alive_npcs:
            self.stats_text.insert(tk.END,
                                   f"{npc.name} ({npc.__class__.__name__}) - Ур. {npc.level}, HP: {npc.health}/{npc.max_health}, "
                                   f"Состояние: {npc.state}, Локация: {npc.current_location.name if npc.current_location else 'Неизвестно'}\n")

        self.stats_text.insert(tk.END, f"\n=== МЕРТВЫЕ ПЕРСОНАЖИ ({len(dead_npcs)}) ===\n")
        for npc in dead_npcs[:5]:  # Показываем только последних 5 мертвых
            self.stats_text.insert(tk.END, f"{npc.name} ({npc.__class__.__name__}) - Ур. {npc.level}\n")

        if len(dead_npcs) > 5:
            self.stats_text.insert(tk.END, f"... и еще {len(dead_npcs) - 5}\n")

        # Обновление состояния кнопок
        self.start_btn.state(["disabled" if self.game_world.is_running else "!disabled"])
        self.stop_btn.state(["disabled" if not self.game_world.is_running else "!disabled"])
        self.add_btn.state(["disabled" if self.game_world.is_running else "!disabled"])


if __name__ == "__main__":
    root = tk.Tk()
    app = GameGUI(root)
    root.mainloop()