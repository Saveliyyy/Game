from abc import ABC, abstractmethod
from enum import Enum
import random


class StatusEffect(Enum):
    POISONED = "Отравление"
    BURNING = "Горение"
    FROZEN = "Заморозка"
    BLESSED = "Благословение"


class SpellType(Enum):
    FIREBALL = "Огненный шар"
    ICE_SHACKLES = "Оковы льда"
    HEAL = "Исцеление"


class NPC(ABC):
    def __init__(self, name):
        self.name = name
        self.health = 100
        self.max_health = 100
        self.level = 1
        self.experience = 0
        self.inventory = []
        self.status_effects = {}
        self.is_alive = True

    @abstractmethod
    def join_party(self):
        pass

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
        return f"{self.name} достигает {self.level} уровня! Здоровье восстановлено."

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
        return f"{self.name} восстанавливает {amount} здоровья. Теперь {self.health}/{self.max_health} HP"


class CombatMixin:
    def attack(self, target, critical_chance=0.1):
        damage = random.randint(8, 15)
        if random.random() < critical_chance:
            damage *= 2
            target.take_damage(damage)
            return f"{self.name} наносит критический удар: -{damage} HP {target.name}"
        target.take_damage(damage)
        return f"{self.name} атакует {target.name}: -{damage} HP"


class SpellcasterMixin:
    def __init__(self):
        self.known_spells = []
        self.mana = 100

    def learn_spell(self, spell: SpellType):
        if spell not in self.known_spells:
            self.known_spells.append(spell)
            return f"{self.name} изучает заклинание: {spell.value}"
        return f"{self.name} уже знает это заклинание"

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
            message += f". {target.name} получает 25 урона и начинает гореть!"

        elif spell == SpellType.ICE_SHACKLES and target:
            target.add_status(StatusEffect.FROZEN, 2)
            message += f". {target.name} заморожен на 2 хода!"

        elif spell == SpellType.HEAL:
            self.heal(30)
            message += f". {self.name} восстанавливает 30 здоровья"

        return message


class Mage(NPC, SpellcasterMixin):
    def __init__(self, name):
        super().__init__(name)
        SpellcasterMixin.__init__(self)
        self.mana = 150
        self.known_spells = [SpellType.ICE_SHACKLES, SpellType.FIREBALL]

    def join_party(self):
        return f"К партии присоединяется маг {self.name}"

    def rest(self):
        self.mana = min(150, self.mana + 50)
        return f"{self.name} медитирует. Мана восстановлена до {self.mana}"


class Warrior(NPC, CombatMixin):
    def __init__(self, name):
        super().__init__(name)
        self.max_health = 150
        self.health = 150

    def join_party(self):
        return f"К партии присоединяется воин {self.name}"

    def shield_bash(self, target):
        damage = 15
        target.take_damage(damage)
        return f"{self.name} бьёт щитом: -{damage} HP {target.name}"


class Rogue(NPC, CombatMixin):
    def __init__(self, name):
        super().__init__(name)
        self.stealth = True

    def join_party(self):
        return f"К партии присоединяется разбойник {self.name}"

    def backstab(self, target):
        if self.stealth:
            self.stealth = False
            return f"{self.name} наносит удар в спину: -30 HP {target.name}"
        return "Нужно скрыться для удара в спину"


class GameWorld:
    def __init__(self):
        self.npcs = []
        self.hazards = {}
        self.event_log = []

    def add_npc(self, npc):
        self.npcs.append(npc)
        self.log_event(npc.join_party())

    def log_event(self, event):
        self.event_log.append(event)

    def add_hazard(self, location, effect, duration):
        self.hazards[location] = (effect, duration)

    def update_world(self):
        # Обновление статусов всех NPC
        for npc in self.npcs:
            status_updates = npc.update_statuses()
            for update in status_updates:
                self.log_event(update)

        # Обновление опасностей
        for location in list(self.hazards.keys()):
            effect, duration = self.hazards[location]
            duration -= 1
            if duration <= 0:
                del self.hazards[location]
                self.log_event(f"Опасность в {location} рассеялась")
            else:
                self.hazards[location] = (effect, duration)

    def simulate_battle(self, rounds=3):
        enemies = [npc for npc in self.npcs if isinstance(npc, (Warrior, Rogue, Mage))]
        for _ in range(rounds):
            attacker = random.choice(enemies)
            target = random.choice([npc for npc in enemies if npc != attacker])

            if isinstance(attacker, Mage) and random.random() > 0.5:
                spell = random.choice(attacker.known_spells)
                event = attacker.cast_spell(spell, target)
            else:
                event = attacker.attack(target)

            self.log_event(event)

            if not target.is_alive:
                self.log_event(f"{attacker.name} получает 50 опыта за победу")
                attacker.gain_exp(50)
                enemies.remove(target)

            self.update_world()


# Пример использования
game = GameWorld()

# Создание персонажей
elrin = Mage("Элрин23")
shaira = Rogue("Шайра17")
grog = Warrior("Грогнак99")

# Добавление в мир
game.add_npc(elrin)
game.add_npc(shaira)
game.add_npc(grog)

# Изучение заклинаний
game.log_event(elrin.learn_spell(SpellType.HEAL))

# Добавление опасности
game.add_hazard("Пещера", StatusEffect.POISONED, 3)

# Симуляция боя
game.simulate_battle(rounds=5)

# Вывод лога
print("\n".join(game.event_log))