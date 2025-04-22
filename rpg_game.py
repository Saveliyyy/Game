import tkinter as tk
from tkinter import ttk, scrolledtext
from PIL import Image, ImageTk
import random
from enum import Enum


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
        self.health = max(0, self.health - damage)
        if self.health == 0:
            self.is_alive = False
            return f"{self.name} повержен!"
        return f"{self.name} теряет {damage} здоровья. Осталось: {self.health} HP"

    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)
        return f"{self.name} восстанавливает {amount} здоровья."

    def attack(self, target):
        """Базовый метод атаки, который могут переопределить подклассы"""
        damage = random.randint(10, 15)
        target.take_damage(damage)
        return f"{self.name} атакует {target.name} и наносит {damage} урона!"


# ========== КЛАССЫ ПЕРСОНАЖЕЙ ==========
class Mage(NPC):
    def __init__(self, name):
        super().__init__(name)
        self.mana = 150
        self.known_spells = [SpellType.ICE_SHACKLES, SpellType.FIREBALL]

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

        return message


class Warrior(NPC):
    def __init__(self, name):
        super().__init__(name)
        self.max_health = 150
        self.health = 150

    def attack(self, target):
        damage = random.randint(15, 25)
        target.take_damage(damage)
        return f"{self.name} мощно атакует {target.name} и наносит {damage} урона!"


class Rogue(NPC):
    def __init__(self, name):
        super().__init__(name)
        self.stealth = True

    def attack(self, target):
        if self.stealth:
            damage = random.randint(20, 35)
            self.stealth = False
            return f"{self.name} бьёт в спину и наносит {damage} урона!"
        else:
            damage = random.randint(10, 15)
            self.stealth = random.choice([True, False])  # 50% шанс скрыться
            return f"{self.name} атакует {target.name} и наносит {damage} урона!"


# ========== СИСТЕМА МИРА ==========
class GameWorld:
    def __init__(self):
        self.npcs = []
        self.event_log = []

    def add_npc(self, npc):
        self.npcs.append(npc)
        self.log_event(npc.join_party())

    def log_event(self, event):
        self.event_log.append(event)

    def simulate_battle(self, rounds=3):
        if len(self.npcs) < 2:
            self.log_event("Нужно как минимум 2 персонажа для боя!")
            return

        for _ in range(rounds):
            # Выбираем только живых персонажей
            alive_npcs = [npc for npc in self.npcs if npc.is_alive]
            if len(alive_npcs) < 2:
                break

            attacker = random.choice(alive_npcs)
            target = random.choice([npc for npc in alive_npcs if npc != attacker])

            if isinstance(attacker, Mage) and random.random() < 0.7:  # 70% шанс использовать заклинание
                spell = random.choice(attacker.known_spells)
                event = attacker.cast_spell(spell, target)
            else:
                event = attacker.attack(target)

            self.log_event(event)

            # Обновляем статусы после атаки
            status_events = target.update_statuses()
            for status_event in status_events:
                self.log_event(status_event)

            # Проверяем, не умер ли кто-то от эффектов
            if not target.is_alive:
                self.log_event(f"{target.name} пал в бою!")


# ========== ГРАФИЧЕСКИЙ ИНТЕРФЕЙС ==========
class GameGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RPG Simulator")
        self.game_world = GameWorld()

        # Создание интерфейса
        self.log_text = scrolledtext.ScrolledText(root, width=60, height=15)
        self.log_text.pack()

        self.add_btn = ttk.Button(root, text="Добавить персонажа", command=self.add_character)
        self.add_btn.pack()

        self.simulate_btn = ttk.Button(root, text="Симуляция боя", command=lambda: self.simulate_battle())
        self.simulate_btn.pack()

    def add_character(self):
        dialog = tk.Toplevel()
        ttk.Label(dialog, text="Имя:").pack()
        name_entry = ttk.Entry(dialog)
        name_entry.pack()

        class_var = tk.StringVar()
        ttk.Combobox(dialog, textvariable=class_var, values=["Маг", "Воин", "Разбойник"]).pack()

        def create():
            name = name_entry.get()
            if class_var.get() == "Маг":
                char = Mage(name)
            elif class_var.get() == "Воин":
                char = Warrior(name)
            else:
                char = Rogue(name)

            self.game_world.add_npc(char)
            self.update_log()
            dialog.destroy()

        ttk.Button(dialog, text="Создать", command=create).pack()

    def simulate_battle(self):
        self.game_world.simulate_battle(3)
        self.update_log()

    def update_log(self):
        self.log_text.delete(1.0, tk.END)
        for event in self.game_world.event_log:
            self.log_text.insert(tk.END, event + "\n")


if __name__ == "__main__":
    root = tk.Tk()
    app = GameGUI(root)
    root.mainloop()