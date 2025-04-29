import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from PIL import Image, ImageTk
import random
from enum import Enum
import threading
import time
import os
from tkinter import PhotoImage
from PIL import Image, ImageTk, ImageDraw, ImageFont

# ========== БАЗОВЫЕ КЛАССЫ ==========
class StatusEffect(Enum):
    POISONED = "Отравление"
    BURNING = "Горение"
    FROZEN = "Заморозка"
    BLESSED = "Благословение"
    REGENERATION = "Регенерация"
    SHIELDED = "Щит"
    STUNNED = "Оглушение"


class SpellType(Enum):
    FIREBALL = "Огненный шар"
    ICE_SHACKLES = "Оковы льда"
    HEAL = "Исцеление"
    LIGHTNING = "Молния"
    HOLY_LIGHT = "Священный свет"
    POISON_CLOUD = "Ядовитое облако"
    SHIELD = "Магический щит"
    STUN = "Оглушение"


class ArtifactType(Enum):
    WEAPON = "Оружие"
    ARMOR = "Броня"
    POTION = "Зелье"
    SCROLL = "Свиток"
    RING = "Кольцо"
    AMULET = "Амулет"
    RELIC = "Реліквія"
    TOME = "Том"


class MonsterType(Enum):
    GOBLIN = "Гоблин"
    ORC = "Орк"
    TROLL = "Тролль"
    DRAGON = "Дракон"
    UNDEAD = "Нежить"
    DEMON = "Демон"
    ELEMENTAL = "Элементаль"


class Artifact:
    def __init__(self, name, artifact_type, power, bonus_type):
        self.name = name
        self.type = artifact_type
        self.power = power
        self.bonus_type = bonus_type

    def __str__(self):
        return f"{self.type.value}: {self.name} ({self.bonus_type} +{self.power})"

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
            "amulet": None,
            "relic": None
        }
        self.gold = random.randint(0, 50)
        self.state = "exploring"
        self.target = None
        self.bonuses = {
            "HP": 0,
            "Мана": 0,
            "Урон": 0,
            "Защита": 0,
            "Крит": 0,
            "Скорость": 0,
            "Регенерация": 0
        }
        self.known_spells = []

    def apply_bonuses(self):
        self.clear_bonuses()
        for item in self.equipment.values():
            if item:
                self.bonuses[item.bonus_type] += item.power

    def clear_bonuses(self):
        for key in self.bonuses:
            self.bonuses[key] = 0

    def join_party(self):
        return f"К партии присоединяется {self.name} ({self.__class__.__name__})"

    def gain_exp(self, amount):
        self.experience += amount
        if self.experience >= 100 * self.level:
            return self.level_up()
        return f"{self.name} получает {amount} опыта."

    def level_up(self):
        self.level += 1
        self.max_health += 20 + self.bonuses["HP"]
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
            elif effect == StatusEffect.REGENERATION:
                self.heal(5 + self.bonuses["Регенерация"])
                results.append(f"{self.name} восстанавливается благодаря регенерации")
            elif effect == StatusEffect.SHIELDED:
                results.append(f"{self.name} защищен магическим щитом")
            elif effect == StatusEffect.STUNNED:
                results.append(f"{self.name} оглушен и пропускает ход")

        return results

    def take_damage(self, damage):
        armor_defense = self.equipment["armor"].power if self.equipment["armor"] else 0
        actual_damage = max(1, damage - (armor_defense // 2 + self.bonuses["Защита"]))

        if StatusEffect.SHIELDED in self.status_effects:
            actual_damage = max(0, actual_damage - 10)

        self.health = max(0, self.health - actual_damage)
        if self.health == 0:
            self.die()
            return f"{self.name} повержен!"
        return f"{self.name} теряет {actual_damage} здоровья. Осталось: {self.health} HP"

    def heal(self, amount):
        heal_amount = min(self.max_health - self.health, amount + self.bonuses["HP"] // 2)
        self.health += heal_amount
        return f"{self.name} восстанавливает {heal_amount} здоровья."

    def attack(self, target):
        """Базовый метод атаки"""
        if StatusEffect.STUNNED in self.status_effects:
            return f"{self.name} оглушен и не может атаковать!"

        weapon_power = self.equipment["weapon"].power if self.equipment["weapon"] else 0
        base_damage = random.randint(5 + weapon_power, 10 + weapon_power * 2)

        # Учет критического урона
        crit_chance = self.bonuses["Крит"] / 100
        if random.random() < crit_chance:
            base_damage *= 2
            damage_msg = f"Критический удар! {base_damage} урона"
        else:
            damage_msg = f"{base_damage} урона"

        total_damage = base_damage + self.bonuses["Урон"]
        result = target.take_damage(total_damage)
        return f"{self.name} атакует {target.name} ({damage_msg}): {result}"

    def cast_spell(self, spell: SpellType, target=None):
        if spell not in self.known_spells:
            return f"{self.name} не знает это заклинание"

        if StatusEffect.STUNNED in self.status_effects:
            return f"{self.name} оглушен и не может кастовать!"

        return "Заклинание не реализовано"

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

        # Встреча с монстром
        if random.random() < self.current_location.danger_level * 0.3:
            monster = self.current_location.get_monster()
            if monster:
                self.state = "fighting"
                self.target = monster
                events.append(f"{self.name} встречает {monster.name} и готовится к бою!")

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
        if self.known_spells and random.random() < 0.5:
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
            exp_gain = random.randint(10, 30) * self.target.power // 10
            events.append(self.gain_exp(exp_gain))
            self.gold += self.target.gold
            events.append(f"{self.name} забирает {self.target.gold} золота у {self.target.name}")
            self.state = "exploring"
            self.target = None

        # Ответный удар
        elif random.random() < 0.8 and self.target.is_alive:
            if isinstance(self.target, Monster):
                events.append(self.target.special_attack(self))
            else:
                events.append(self.target.attack(self))

            # Проверка статусов
            status_events = self.update_statuses()
            events.extend(status_events)

            if not self.is_alive:
                events.append(f"{self.name} был убит {self.target.name}!")
                if isinstance(self.target, NPC):
                    self.target.gain_exp(random.randint(15, 25))
                    self.target.gold += self.gold // 2
                    events.append(f"{self.target.name} забирает {self.gold // 2} золота у {self.name}")

        return events

    def rest(self):
        if not self.is_alive:
            return []

        events = []
        heal_amount = random.randint(5, 15) + self.bonuses["Регенерация"]
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
            event = random.choice([
                f"{self.name} размышляет о жизни...",
                f"{self.name} чистит свое снаряжение",
                f"{self.name} перекусывает"
            ])
            events.append(event)

        # Возвращение к исследованию
        if self.health > self.max_health * 0.7 or random.random() < 0.5:
            self.state = "exploring"
            events.append(f"{self.name} возобновляет исследование.")

        return events

    def update(self, world):
        if not self.is_alive:
            return []

        events = []
        self.apply_bonuses()

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
        elif artifact.type == ArtifactType.RELIC:
            slot = "relic"
        else:
            return f"{artifact.name} нельзя экипировать"

        old_item = self.equipment[slot]
        if old_item:
            self.inventory.append(old_item)

        self.equipment[slot] = artifact
        self.inventory.remove(artifact)
        return f"{self.name} экипирует {artifact.name}"

class Monster(NPC):
    def __init__(self, name, monster_type, power):
        super().__init__(name)
        self.monster_type = monster_type
        self.power = power
        self.health = power * 2
        self.max_health = self.health
        self.gold = random.randint(5, 20) * power // 10

    def special_attack(self, target):
        attacks = {
            MonsterType.DRAGON: ("Огненное дыхание", 50),
            MonsterType.UNDEAD: ("Проклятие", 30),
            MonsterType.DEMON: ("Адское пламя", 40),
            MonsterType.TROLL: ("Мощный удар", 35),
            MonsterType.GOBLIN: ("Грязный трюк", 20),
            MonsterType.ORC: ("Берсеркерская ярость", 30),
            MonsterType.ELEMENTAL: ("Стихийный удар", 45)
        }
        name, base_damage = attacks.get(self.monster_type, ("Атака", 25))
        damage = base_damage + random.randint(0, self.power)
        result = target.take_damage(damage)

        # Специальные эффекты
        if self.monster_type == MonsterType.UNDEAD:
            target.add_status(StatusEffect.POISONED, 3)
        elif self.monster_type == MonsterType.DEMON:
            target.add_status(StatusEffect.BURNING, 2)
        elif self.monster_type == MonsterType.ELEMENTAL:
            target.add_status(StatusEffect.FROZEN if random.random() < 0.5 else StatusEffect.BURNING, 2)
        return f"{self.name} использует {name}! {result}"

class Location:
    def __init__(self, name, danger_level):
        self.name = name
        self.danger_level = danger_level
        self.artifacts = []
        self.monsters = []
        self.generate_content()

    def generate_content(self):
        # Генерация артефактов
        artifact_count = random.randint(0, 3 + self.danger_level)
        bonus_types = [
            "HP", "Мана", "Урон", "Защита",
            "Крит", "Скорость", "Регенерация"
        ]
        for _ in range(artifact_count):
            artifact_type = random.choice(list(ArtifactType))
            power = random.randint(1, 10) * self.danger_level
            bonus_type = random.choice(bonus_types)

            names = {
                ArtifactType.WEAPON: ["Меч", "Топор", "Кинжал", "Посох", "Лук", "Молот"],
                ArtifactType.ARMOR: ["Доспех", "Щит", "Шлем", "Перчатки", "Сапоги"],
                ArtifactType.POTION: ["Зелье здоровья", "Зелье маны", "Яд", "Эликсир"],
                ArtifactType.SCROLL: ["Свиток огня", "Свиток льда", "Свиток молнии"],
                ArtifactType.RING: ["Кольцо силы", "Кольцо защиты", "Кольцо магии"],
                ArtifactType.AMULET: ["Амулет здоровья", "Амулет маны", "Амулет защиты"],
                ArtifactType.RELIC: ["Реліквія древних", "Священный артефакт"],
                ArtifactType.TOME: ["Том знаний", "Гримуар"]
            }
            name = random.choice(names.get(artifact_type, ["Таинственный предмет"]))
            self.artifacts.append(Artifact(name, artifact_type, power, bonus_type))

        # Генерация монстров
        monster_count = random.randint(1, 2 + self.danger_level)
        for _ in range(monster_count):
            monster_type = random.choice(list(MonsterType))
            power = random.randint(5, 15) * self.danger_level
            name = f"{monster_type.value} ур.{self.danger_level}"
            self.monsters.append(Monster(name, monster_type, power))

    def get_artifact(self):
        if self.artifacts:
            return self.artifacts.pop()
        return None

    def get_monster(self):
        if self.monsters:
            return random.choice(self.monsters)
        return None

# ========== КЛАССЫ ИГРОВЫХ ПЕРСОНАЖЕЙ ==========
class Mage(NPC):
    def __init__(self, name):
        super().__init__(name)
        self.mana = 150 + random.randint(0, 50)
        self.max_mana = self.mana
        self.known_spells = [SpellType.FIREBALL, SpellType.ICE_SHACKLES]
        self.bonuses["Мана"] += 20

    def cast_spell(self, spell: SpellType, target=None):
        base_result = super().cast_spell(spell, target)
        if "не может" in base_result or "не знает" in base_result:
            return base_result

        if self.mana < 20:
            return "Недостаточно маны"

        self.mana -= 20
        message = f"{self.name} кастует {spell.value}"

        if spell == SpellType.FIREBALL and target:
            damage = 25 + self.bonuses["Урон"]
            target.take_damage(damage)
            target.add_status(StatusEffect.BURNING, 3)
            message += f". {target.name} получает {damage} урона!"

        elif spell == SpellType.ICE_SHACKLES and target:
            target.add_status(StatusEffect.FROZEN, 2)
            message += f". {target.name} заморожен!"

        return message


class Archmage(Mage):
    def __init__(self, name):
        super().__init__(name)
        self.known_spells.append(SpellType.LIGHTNING)
        self.known_spells.append(SpellType.SHIELD)
        self.bonuses["Урон"] += 10
        self.bonuses["Мана"] += 30

    def cast_spell(self, spell: SpellType, target=None):
        if spell == SpellType.LIGHTNING and target:
            if self.mana < 30:
                return "Недостаточно маны"
            self.mana -= 30
            damage = 40 + self.bonuses["Урон"]
            target.take_damage(damage)
            return f"{self.name} поражает {target.name} молнией ({damage} урона)"

        elif spell == SpellType.SHIELD:
            if self.mana < 25:
                return "Недостаточно маны"
            self.mana -= 25
            self.add_status(StatusEffect.SHIELDED, 3)
            return f"{self.name} создает магический щит"

        return super().cast_spell(spell, target)


class Necromancer(Mage):
    def __init__(self, name):
        super().__init__(name)
        self.known_spells.append(SpellType.POISON_CLOUD)
        self.bonuses["Регенерация"] += 5
        self.max_health += 20

    def cast_spell(self, spell: SpellType, target=None):
        if spell == SpellType.POISON_CLOUD and target:
            if self.mana < 35:
                return "Недостаточно маны"
            self.mana -= 35
            target.add_status(StatusEffect.POISONED, 4)
            return f"{self.name} создает ядовитое облако вокруг {target.name}"
        return super().cast_spell(spell, target)


class Warrior(NPC):
    def __init__(self, name):
        super().__init__(name)
        self.max_health = 150 + random.randint(0, 30)
        self.health = self.max_health
        self.bonuses["Защита"] += 5

    def attack(self, target):
        weapon_power = self.equipment["weapon"].power if self.equipment["weapon"] else 0
        damage = random.randint(15 + weapon_power, 25 + weapon_power * 2) + self.bonuses["Урон"]
        return f"{self.name} мощно атакует {target.name}: {target.take_damage(damage)}"


class Berserker(Warrior):
    def __init__(self, name):
        super().__init__(name)
        self.bonuses["Урон"] += 15
        self.bonuses["Защита"] -= 3
        self.max_health += 20

    def attack(self, target):
        damage_bonus = self.max_health - self.health  # Чем меньше HP, тем сильнее атака
        weapon_power = self.equipment["weapon"].power if self.equipment["weapon"] else 0
        damage = random.randint(20 + weapon_power, 30 + weapon_power * 2) + damage_bonus // 2
        return f"{self.name} впадает в ярость! {target.take_damage(damage)}"


class Paladin(Warrior):
    def __init__(self, name):
        super().__init__(name)
        self.known_spells = [SpellType.HEAL, SpellType.HOLY_LIGHT]
        self.bonuses["Защита"] += 10
        self.max_health += 30

    def cast_spell(self, spell: SpellType, target=None):
        if spell == SpellType.HEAL:
            if target:
                heal_amount = 30 + self.bonuses["HP"]
                return f"{self.name} исцеляет {target.name}: {target.heal(heal_amount)}"
        elif spell == SpellType.HOLY_LIGHT:
            if isinstance(self.target, Monster) and self.target.monster_type == MonsterType.UNDEAD:
                damage = 50 + self.bonuses["Урон"]
                return f"{self.name} изгоняет нечисть: {self.target.take_damage(damage)}"
            return f"{self.name} излучает священный свет, но ничего не происходит"
        return super().cast_spell(spell, target)

class Rogue(NPC):
    def __init__(self, name):
        super().__init__(name)
        self.stealth = True
        self.bonuses["Крит"] += 15
        self.bonuses["Скорость"] += 5

    def attack(self, target):
        if self.stealth:
            weapon_power = self.equipment["weapon"].power if self.equipment["weapon"] else 0
            damage = random.randint(20 + weapon_power * 2, 35 + weapon_power * 2) + self.bonuses["Урон"]
            self.stealth = False
            return f"{self.name} бьёт в спину: {target.take_damage(damage)}"
        else:
            weapon_power = self.equipment["weapon"].power if self.equipment["weapon"] else 0
            damage = random.randint(10 + weapon_power, 15 + weapon_power) + self.bonuses["Урон"]
            self.stealth = random.random() < 0.5  # 50% шанс скрыться
            return f"{self.name} атакует {target.name}: {target.take_damage(damage)}"


class Assassin(Rogue):
    def __init__(self, name):
        super().__init__(name)
        self.bonuses["Урон"] += 20
        self.bonuses["Защита"] -= 5
        self.known_spells = [SpellType.POISON_CLOUD]

    def attack(self, target):
        result = super().attack(target)
        if not self.stealth and random.random() < 0.3:
            target.add_status(StatusEffect.POISONED, 3)
            result += f" и отравляет {target.name}"
        return result


class Shadowdancer(Rogue):
    def __init__(self, name):
        super().__init__(name)
        self.bonuses["Скорость"] += 10
        self.bonuses["Крит"] += 10
        self.known_spells = [SpellType.STUN]

    def cast_spell(self, spell: SpellType, target=None):
        if spell == SpellType.STUN and target:
            target.add_status(StatusEffect.STUNNED, 2)
            return f"{self.name} оглушает {target.name}"
        return super().cast_spell(spell, target)


class Priest(NPC):
    def __init__(self, name):
        super().__init__(name)
        self.mana = 100
        self.max_mana = 100
        self.known_spells = [SpellType.HEAL, SpellType.HOLY_LIGHT]
        self.bonuses["HP"] += 30

    def cast_spell(self, spell: SpellType, target=None):
        if spell == SpellType.HEAL:
            if self.mana < 25:
                return "Недостаточно маны"
            self.mana -= 25
            heal_amount = 40 + self.bonuses["HP"]
            if target:
                return f"{self.name} исцеляет {target.name}: {target.heal(heal_amount)}"
            return f"{self.name} исцеляет себя: {self.heal(heal_amount)}"

        elif spell == SpellType.HOLY_LIGHT:
            if self.mana < 40:
                return "Недостаточно маны"
            self.mana -= 40
            if isinstance(self.target, Monster) and self.target.monster_type in [MonsterType.UNDEAD, MonsterType.DEMON]:
                damage = 35 + self.bonuses["Урон"]
                return f"{self.name} изгоняет нечисть: {self.target.take_damage(damage)}"
            return f"{self.name} излучает священный свет, но ничего не происходит"

        return super().cast_spell(spell, target)


class Inquisitor(Priest):
    def __init__(self, name):
        super().__init__(name)
        self.known_spells.append(SpellType.FIREBALL)
        self.bonuses["Урон"] += 10
        self.bonuses["Мана"] += 20

    def cast_spell(self, spell: SpellType, target=None):
        if spell == SpellType.FIREBALL and target:
            if self.mana < 30:
                return "Недостаточно маны"
            self.mana -= 30
            damage = 30 + self.bonuses["Урон"]
            target.take_damage(damage)
            if isinstance(target, Monster) and target.monster_type == MonsterType.UNDEAD:
                damage *= 1.5
                target.take_damage(damage)
                return f"{self.name} сжигает нежить священным огнем: {damage} урона"
            return f"{self.name} метает огненный шар: {damage} урона"
        return super().cast_spell(spell, target)


class Druid(Priest):
    def __init__(self, name):
        super().__init__(name)
        self.known_spells.append(SpellType.ICE_SHACKLES)
        self.bonuses["Регенерация"] += 10
        self.max_health += 20

    def cast_spell(self, spell: SpellType, target=None):
        if spell == SpellType.ICE_SHACKLES and target:
            if self.mana < 25:
                return "Недостаточно маны"
            self.mana -= 25
            target.add_status(StatusEffect.FROZEN, 2)
            target.add_status(StatusEffect.REGENERATION, 3)  # Друид замораживает и одновременно лечит
            return f"{self.name} сковывает {target.name} льдом и дает регенерацию"
        return super().cast_spell(spell, target)

class Archer(NPC):
    def __init__(self, name):
        super().__init__(name)
        self.bonuses["Крит"] += 20
        self.bonuses["Скорость"] += 10
        self.max_health += 10

    def attack(self, target):
        weapon_power = self.equipment["weapon"].power if self.equipment["weapon"] else 0
        base_damage = random.randint(10 + weapon_power, 20 + weapon_power)

        # Учет критического урона
        crit_chance = (self.bonuses["Крит"] + 20) / 100  # +20% базовый шанс крита для лучника
        if random.random() < crit_chance:
            base_damage *= 2.5  # Больший множитель крита для лучника
            damage_msg = f"Критический выстрел! {base_damage} урона"
        else:
            damage_msg = f"{base_damage} урона"

        total_damage = base_damage + self.bonuses["Урон"]
        result = target.take_damage(total_damage)
        return f"{self.name} стреляет в {target.name} ({damage_msg}): {result}"


class Sniper(Archer):
    def __init__(self, name):
        super().__init__(name)
        self.bonuses["Урон"] += 15
        self.bonuses["Скорость"] += 5
        self.bonuses["Крит"] += 10

    def attack(self, target):
        # Снайпер имеет шанс на мгновенное убийство слабых врагов
        if isinstance(target, Monster) and target.health < target.max_health * 0.3 and random.random() < 0.3:
            target.health = 0
            target.die()
            return f"{self.name} убивает {target.name} одним точным выстрелом!"
        return super().attack(target)


class Ranger(Archer):
    def __init__(self, name):
        super().__init__(name)
        self.known_spells = [SpellType.POISON_CLOUD]
        self.bonuses["Регенерация"] += 5
        self.max_health += 20

    def cast_spell(self, spell: SpellType, target=None):
        if spell == SpellType.POISON_CLOUD and target:
            target.add_status(StatusEffect.POISONED, 4)
            return f"{self.name} стреляет отравленной стрелой в {target.name}"
        return super().cast_spell(spell, target)


class Alchemist(NPC):
    def __init__(self, name):
        super().__init__(name)
        self.bonuses["Регенерация"] += 15
        self.max_health += 50
        self.known_spells = [SpellType.POISON_CLOUD]

    def cast_spell(self, spell: SpellType, target=None):
        if spell == SpellType.POISON_CLOUD and target:
            target.add_status(StatusEffect.POISONED, 5)
            return f"{self.name} бросает ядовитую бомбу в {target.name}"
        return super().cast_spell(spell, target)

    def rest(self):
        events = super().rest()
        # Алхимик создает зелья во время отдыха
        if random.random() < 0.5:
            potion_type = random.choice(["health", "mana"])
            power = random.randint(5, 15)
            potion = Artifact(f"Зелье {'здоровья' if potion_type == 'health' else 'маны'}",
                              ArtifactType.POTION, power, "HP" if potion_type == "health" else "Мана")
            self.inventory.append(potion)
            events.append(f"{self.name} создает {potion.name} во время отдыха")
        return events


class Bomber(Alchemist):
    def __init__(self, name):
        super().__init__(name)
        self.known_spells.append(SpellType.FIREBALL)
        self.bonuses["Урон"] += 10
        self.max_health -= 20

    def cast_spell(self, spell: SpellType, target=None):
        if spell == SpellType.FIREBALL and target:
            damage = 40 + self.bonuses["Урон"]
            target.take_damage(damage)
            target.add_status(StatusEffect.BURNING, 3)
            return f"{self.name} бросает взрывную смесь: {damage} урона"
        return super().cast_spell(spell, target)


class Transmuter(Alchemist):
    def __init__(self, name):
        super().__init__(name)
        self.bonuses["Мана"] += 50
        self.known_spells = [SpellType.HEAL, SpellType.SHIELD]

    def cast_spell(self, spell: SpellType, target=None):
        if spell == SpellType.SHIELD:
            if target:
                target.add_status(StatusEffect.SHIELDED, 4)
                return f"{self.name} создает защитный барьер вокруг {target.name}"
            self.add_status(StatusEffect.SHIELDED, 4)
            return f"{self.name} создает защитный барьер"
        return super().cast_spell(spell, target)


# ========== КЛАСС МОНСТРА ==========
class Monster(NPC):
    def __init__(self, name, monster_type, power):
        super().__init__(name)
        self.monster_type = monster_type
        self.power = power
        self.health = power * 2
        self.max_health = self.health
        self.gold = random.randint(5, 20) * power // 10

    def special_attack(self, target):
        attacks = {
            MonsterType.DRAGON: ("Огненное дыхание", 50),
            MonsterType.UNDEAD: ("Проклятие", 30),
            MonsterType.DEMON: ("Адское пламя", 40),
            MonsterType.TROLL: ("Мощный удар", 35),
            MonsterType.GOBLIN: ("Грязный трюк", 20),
            MonsterType.ORC: ("Берсеркерская ярость", 30),
            MonsterType.ELEMENTAL: ("Стихийный удар", 45)
        }
        name, base_damage = attacks.get(self.monster_type, ("Атака", 25))
        damage = base_damage + random.randint(0, self.power)
        result = target.take_damage(damage)

        # Специальные эффекты
        if self.monster_type == MonsterType.UNDEAD:
            target.add_status(StatusEffect.POISONED, 3)
        elif self.monster_type == MonsterType.DEMON:
            target.add_status(StatusEffect.BURNING, 2)
        elif self.monster_type == MonsterType.ELEMENTAL:
            target.add_status(StatusEffect.FROZEN if random.random() < 0.5 else StatusEffect.BURNING, 2)
        return f"{self.name} использует {name}! {result}"


# ========== СИСТЕМА МИРА ==========
class GameWorld:
    def __init__(self):
        self.npcs = []
        self.monsters = []
        self.locations = [
            Location("Лес", 1),
            Location("Пещеры", 2),
            Location("Горы", 3),
            Location("Подземелье", 4),
            Location("Храм", 3),
            Location("Лаборатория", 5)
        ]
        self.event_log = []
        self.is_running = False
        self.simulation_speed = 1.0
        self.turn_count = 0

    def add_npc(self, npc):
        self.npcs.append(npc)
        self.log_event(npc.join_party())

    def add_multiple_npcs(self, npc_list):
        for npc in npc_list:
            self.add_npc(npc)

    def log_event(self, event):
        self.event_log.append(event)
        if len(self.event_log) > 1000:
            self.event_log = self.event_log[-1000:]

    def simulate_turn(self):
        if not self.is_running:
            return

        self.turn_count += 1
        events = []

        # Обновляем всех NPC
        for npc in self.npcs:
            if npc.is_alive:
                npc_events = npc.update(self)
                for event in npc_events:
                    self.log_event(event)

        # Обновляем всех монстров
        for monster in list(self.monsters):
            if monster.is_alive:
                monster_events = monster.update(self)
                for event in monster_events:
                    self.log_event(event)
            else:
                self.monsters.remove(monster)

        # Генерация случайных событий
        if random.random() < 0.1:
            event = random.choice([
                "Над миром проносится странный ветер...",
                "Где-то вдалеке слышен странный шум",
                "Небо на мгновение становится красным",
                "Земля слегка дрожит под ногами",
                "В воздухе ощущается магическая энергия"
            ])
            self.log_event(event)

        # Генерация новых монстров
        if self.turn_count % 5 == 0:
            for location in self.locations:
                if random.random() < 0.3:
                    monster = location.get_monster()
                    if monster:
                        self.monsters.append(monster)
                        self.log_event(f"В локации {location.name} появился {monster.name}")

    def start_simulation(self):
        self.is_running = True
        self.log_event("=== СИМУЛЯЦИЯ НАЧИНАЕТСЯ ===")
        self.turn_count = 0

    def stop_simulation(self):
        self.is_running = False
        self.log_event("=== СИМУЛЯЦИЯ ОСТАНОВЛЕНА ===")

    def get_stats(self):
        stats = {
            "alive_npcs": [npc for npc in self.npcs if npc.is_alive],
            "dead_npcs": [npc for npc in self.npcs if not npc.is_alive],
            "alive_monsters": len([m for m in self.monsters if m.is_alive]),
            "locations": len(self.locations),
            "turn_count": self.turn_count
        }
        return stats


# ========== ГРАФИЧЕСКИЙ ИНТЕРФЕЙС ==========
class GameGUI:
    def __init__(self, root):
        self.root = root
        self.game_world = GameWorld()
        self.simulation_thread = None
        self.class_images = {}  # Для хранения изображений классов
        self.prev_log_length = 0  # Добавляем инициализацию
        self.image_dir = os.path.join(os.path.dirname(__file__), "images")
        self.load_images()

        # Инициализируем кнопки как None
        self.stop_btn = None
        self.start_btn = None
        self.add_btn = None
        self.add_multiple_btn = None

        self.load_images()

        # Цвета для разных типов сообщений
        self.log_colors = {
            "system": "#81a1c1",  # Системные сообщения
            "combat": "#bf616a",  # Боевые сообщения
            "heal": "#a3be8c",  # Исцеление
            "loot": "#ebcb8b",  # Находки, золото
            "level": "#b48ead",  # Уровни, опыт
            "spell": "#88c0d0",  # Заклинания
            "status": "#d08770",  # Статусные эффекты
            "death": "#bf616a",  # Смерть
            "monster": "#d08770",  # Монстры
            "default": "#d8dee9"  # Стандартный цвет
        }

        self.classes = {
            "Маг": ["Архимаг", "Некромант"],
            "Воин": ["Берсерк", "Паладин"],
            "Разбойник": ["Ассасин", "Теневой плясун"],
            "Жрец": ["Инквизитор", "Друид"],
            "Лучник": ["Снайпер", "Рейнджер"],
            "Алхимик": ["Бомбардир", "Трансмутатор"]
        }

        self.setup_main_window()
        self.setup_styles()
        self.create_widgets()
        self.center_window()
        self.setup_event_handlers()
        self.update_ui()

    def load_images(self):
        """Загрузка изображений для классов с улучшенной обработкой ошибок"""
        self.class_images = {}
        icon_mapping = {
            "Маг": "mage.png",
            "Воин": "warrior.png",
            "Разбойник": "rogue.png",
            "Жрец": "priest.png",
            "Лучник": "archer.png",
            "Алхимик": "alchemist.png"
        }

        # Создаем папку images, если ее нет
        if not os.path.exists(self.image_dir):
            os.makedirs(self.image_dir)
            print(f"Создана папка для изображений: {self.image_dir}")

        # Иконка приложения (пробуем несколько форматов)
        icon_formats = ['app_icon.ico', 'app_icon.png']
        for icon_file in icon_formats:
            try:
                icon_path = os.path.join(self.image_dir, icon_file)
                self.root.iconbitmap(icon_path)
                break
            except:
                continue

        # Загрузка иконок классов
        for class_name, filename in icon_mapping.items():
            try:
                img_path = os.path.join(self.image_dir, filename)
                if os.path.exists(img_path):
                    img = Image.open(img_path).resize((64, 64))
                    self.class_images[class_name] = ImageTk.PhotoImage(img)
                else:
                    raise FileNotFoundError(f"Файл {filename} не найден")
            except Exception as e:
                print(f"Ошибка загрузки изображения {filename}: {e}")
                # Создаем текстовую заглушку
                img = Image.new('RGB', (64, 64), color='#3b4252')
                draw = ImageDraw.Draw(img)

                # Настройки текста
                try:
                    font = ImageFont.truetype("arial.ttf", 12)
                except:
                    font = ImageFont.load_default()

                # Рисуем текст по центру
                text = class_name[:3]
                text_width, text_height = draw.textsize(text, font=font)
                position = ((64 - text_width) // 2, (64 - text_height) // 2)

                draw.text(position, text, fill="#ffffff", font=font)
                self.class_images[class_name] = ImageTk.PhotoImage(img)

    def setup_main_window(self):
        """Настройка главного окна"""
        self.root.title("RPG World Simulator")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2e3440')
        self.root.minsize(1000, 700)

        # Иконка приложения
        try:
            self.root.iconbitmap('images/icon.ico')
        except:
            pass

    def setup_styles(self):
        """Настройка кастомных стилей в RPG-стиле"""
        style = ttk.Style()

        # Создаем свою тему
        style.theme_create('rpg_theme', settings={
            ".": {
                "configure": {
                    "background": "#3b4252",
                    "foreground": "#e5e9f0",
                    "font": ("Georgia", 10)
                }
            },
            "TFrame": {
                "configure": {
                    "background": "#3b4252",
                    "relief": "ridge",
                    "borderwidth": 2
                }
            },
            "TLabel": {
                "configure": {
                    "background": "#3b4252",
                    "foreground": "#e5e9f0",
                    "font": ("Georgia", 10)
                }
            },
            "TButton": {
                "configure": {
                    "background": "#5e81ac",
                    "foreground": "#eceff4",
                    "font": ("Georgia", 10, "bold"),
                    "borderwidth": 2,
                    "relief": "raised",
                    "padding": 8,
                    "width": 15
                },
                "map": {
                    "background": [("active", "#81a1c1"), ("disabled", "#4c566a")],
                    "foreground": [("disabled", "#d8dee9")]
                }
            },
            "TLabelFrame": {
                "configure": {
                    "font": ("Papyrus", 12, "bold"),
                    "relief": "groove",
                    "borderwidth": 3,
                    "background": "#3b4252",
                    "foreground": "#d8dee9"
                }
            },
            "TScale": {
                "configure": {
                    "background": "#3b4252",
                    "troughcolor": "#434c5e",
                    "gripcount": 0,
                    "sliderthickness": 15
                }
            },
            "TScrollbar": {
                "configure": {
                    "arrowcolor": "#5e81ac",
                    "troughcolor": "#434c5e",
                    "background": "#5e81ac"
                }
            },
            "TCombobox": {
                "configure": {
                    "fieldbackground": "#434c5e",
                    "background": "#4c566a",
                    "foreground": "#e5e9f0"
                }
            }
        })
        style.theme_use('rpg_theme')

    def create_widgets(self):
        """Создание всех элементов интерфейса"""
        # Главный контейнер
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Панель управления
        self.create_control_panel()

        # Основная область контента
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # Лог событий
        self.create_log_panel()

        # Статистика и информация
        self.create_stats_panel()

        # Меню
        self.create_menu()

    def create_control_panel(self):
        """Панель управления с кнопками"""
        control_frame = ttk.LabelFrame(
            self.main_frame,
            text=" Управление симуляцией ",
            padding=(10, 10)
        )
        control_frame.pack(fill=tk.X, pady=(0, 10))

        # Фрейм для кнопок
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X)

        # Стилизованные кнопки
        buttons = [
            ("Добавить героя", self.add_character, "#5e81ac"),
            ("Создать отряд", self.add_multiple_characters, "#a3be8c"),
            ("Начать приключение", self.start_simulation, "#bf616a"),
            ("Завершить", self.stop_simulation, "#d08770")
        ]

        # Создаем кнопки и сохраняем ссылки на них
        self.buttons = {}
        for text, command, color in buttons:
            btn = tk.Button(
                btn_frame,
                text=text,
                command=command,
                bg=color,
                fg="#2e3440",
                activebackground="#81a1c1",
                activeforeground="#2e3440",
                font=("Georgia", 10, "bold"),
                relief="raised",
                bd=3,
                padx=10,
                pady=5
            )
            btn.pack(side=tk.LEFT, padx=5, expand=True)
            self.buttons[text.split()[0].lower()] = btn

        # Сохраняем ссылки на кнопки в атрибуты
        self.add_btn = self.buttons['добавить']
        self.add_multiple_btn = self.buttons['создать']
        self.start_btn = self.buttons['начать']
        self.stop_btn = self.buttons['завершить']

        # Отключаем кнопку остановки по умолчанию
        self.stop_btn.config(state=tk.DISABLED)

        # Панель скорости симуляции
        speed_frame = ttk.Frame(control_frame)
        speed_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(
            speed_frame,
            text="Скорость времени:",
            font=("Georgia", 10, "italic")
        ).pack(side=tk.LEFT)

        self.speed_var = tk.DoubleVar(value=1.0)
        self.speed_scale = ttk.Scale(
            speed_frame,
            from_=0.1,
            to=5.0,
            variable=self.speed_var,
            command=self.update_speed
        )
        self.speed_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        self.speed_label = ttk.Label(
            speed_frame,
            text="1.0x",
            width=5,
            font=("Georgia", 10, "bold")
        )
        self.speed_label.pack(side=tk.LEFT)

    def create_log_panel(self):
        """Панель журнала событий"""
        log_frame = ttk.LabelFrame(
            self.content_frame,
            text=" Хроники приключений ",
            padding=(10, 10)
        )
        log_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Создаем текстовое поле с тегами для цветов
        self.log_text = tk.Text(
            log_frame,
            wrap=tk.WORD,
            width=60,
            height=25,
            font=('Courier New', 10),
            bg='#2e3440',
            fg='#d8dee9',
            insertbackground='white',
            selectbackground='#5e81ac',
            padx=10,
            pady=10,
            relief='sunken',
            bd=3
        )

        # Настраиваем полосу прокрутки
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

        # Добавляем теги для цветного текста
        for tag_name, color in self.log_colors.items():
            self.log_text.tag_config(tag_name, foreground=color)

        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)

    def create_stats_panel(self):
        """Панель статистики и информации"""
        stats_frame = ttk.LabelFrame(
            self.content_frame,
            text=" Сведения о героях ",
            padding=(10, 10),
            width=300
        )
        stats_frame.pack(side=tk.LEFT, fill=tk.BOTH)

        # Холст для фонового изображения
        self.stats_canvas = tk.Canvas(
            stats_frame,
            bg='#2e3440',
            highlightthickness=0
        )
        self.stats_canvas.pack(fill=tk.BOTH, expand=True)

        # Добавляем полосу прокрутки
        scrollbar = ttk.Scrollbar(stats_frame, command=self.stats_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.stats_canvas.config(yscrollcommand=scrollbar.set)

        # Фрейм для содержимого внутри холста
        self.stats_inner_frame = ttk.Frame(self.stats_canvas)
        self.stats_canvas.create_window((0, 0), window=self.stats_inner_frame, anchor="nw")

        # Привязка для прокрутки
        self.stats_inner_frame.bind(
            "<Configure>",
            lambda e: self.stats_canvas.configure(
                scrollregion=self.stats_canvas.bbox("all")
            )
        )

        # Заголовок статистики
        ttk.Label(
            self.stats_inner_frame,
            text="Статистика мира",
            font=("Papyrus", 14, "bold"),
            foreground="#88c0d0"
        ).pack(pady=(0, 10))

        # Метки для отображения статистики
        self.turn_label = ttk.Label(
            self.stats_inner_frame,
            text="Ход: 0",
            font=("Georgia", 10)
        )
        self.turn_label.pack(anchor="w")

        self.locations_label = ttk.Label(
            self.stats_inner_frame,
            text="Локации: 0",
            font=("Georgia", 10)
        )
        self.locations_label.pack(anchor="w")

        self.monsters_label = ttk.Label(
            self.stats_inner_frame,
            text="Монстры: 0",
            font=("Georgia", 10)
        )
        self.monsters_label.pack(anchor="w")

        # Разделитель
        ttk.Separator(self.stats_inner_frame).pack(fill=tk.X, pady=10)

        # Заголовок списка персонажей
        self.heroes_label = ttk.Label(
            self.stats_inner_frame,
            text="Герои (0)",
            font=("Papyrus", 12, "bold"),
            foreground="#a3be8c"
        )
        self.heroes_label.pack()

        # Фрейм для списка персонажей
        self.heroes_frame = ttk.Frame(self.stats_inner_frame)
        self.heroes_frame.pack(fill=tk.X)

        # Разделитель
        ttk.Separator(self.stats_inner_frame).pack(fill=tk.X, pady=10)

        # Заголовок списка погибших
        self.dead_label = ttk.Label(
            self.stats_inner_frame,
            text="Погибшие (0)",
            font=("Papyrus", 12, "bold"),
            foreground="#bf616a"
        )
        self.dead_label.pack()

        # Фрейм для списка погибших
        self.dead_heroes_frame = ttk.Frame(self.stats_inner_frame)
        self.dead_heroes_frame.pack(fill=tk.X)

    def create_menu(self):
        """Создание меню в стиле RPG"""
        menubar = tk.Menu(self.root, bg="#3b4252", fg="#e5e9f0", activebackground="#4c566a")

        # Меню "Герои"
        hero_menu = tk.Menu(menubar, tearoff=0, bg="#3b4252", fg="#e5e9f0")
        hero_menu.add_command(
            label="Создать героя",
            command=self.add_character,
            accelerator="Ctrl+N"
        )
        hero_menu.add_command(
            label="Создать отряд",
            command=self.add_multiple_characters,
            accelerator="Ctrl+G"
        )
        hero_menu.add_separator()
        hero_menu.add_command(label="Выйти", command=self.on_close, accelerator="Ctrl+Q")
        menubar.add_cascade(label="Герои", menu=hero_menu)

        # Меню "Мир"
        world_menu = tk.Menu(menubar, tearoff=0)
        world_menu.add_command(
            label="Начать приключение",
            command=self.start_simulation,
            accelerator="F5"
        )
        world_menu.add_command(
            label="Остановить время",
            command=self.stop_simulation,
            accelerator="F6"
        )
        world_menu.add_separator()
        world_menu.add_command(
            label="Очистить лог",
            command=self.clear_log,
            accelerator="Ctrl+L"
        )
        menubar.add_cascade(label="Мир", menu=world_menu)

        # Меню "Помощь"
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(
            label="Справка",
            command=self.show_help,
            accelerator="F1"
        )
        help_menu.add_separator()
        help_menu.add_command(
            label="О программе",
            command=self.show_about
        )
        menubar.add_cascade(label="Помощь", menu=help_menu)

        self.root.config(menu=menubar)

    def setup_event_handlers(self):
        """Настройка обработчиков событий"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Горячие клавиши
        self.root.bind('<Control-q>', lambda e: self.on_close())
        self.root.bind('<Control-n>', lambda e: self.add_character())
        self.root.bind('<Control-g>', lambda e: self.add_multiple_characters())
        self.root.bind('<F1>', lambda e: self.show_help())
        self.root.bind('<F5>', lambda e: self.start_simulation())
        self.root.bind('<F6>', lambda e: self.stop_simulation())
        self.root.bind('<Control-l>', lambda e: self.clear_log())

    def center_window(self):
        """Центрирование окна на экране"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def update_speed(self, event=None):
        """Обновление скорости симуляции"""
        speed = round(self.speed_var.get(), 1)
        self.game_world.simulation_speed = speed
        self.speed_label.config(text=f"{speed}x")

    def clear_log(self):
        """Очистка лога событий"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.game_world.event_log = []

    def on_close(self):
        """Обработчик закрытия окна"""
        self.stop_simulation()
        if messagebox.askokcancel(
                "Завершение приключения",
                "Вы уверены, что хотите покинуть этот мир?",
                parent=self.root
        ):
            self.root.destroy()

    def show_help(self):
        """Показать окно помощи"""
        help_window = tk.Toplevel(self.root)
        help_window.title("Мудрость старца")
        help_window.geometry("600x450")
        help_window.resizable(False, False)

        # Стилизованное окно помощи
        help_text = tk.Text(
            help_window,
            wrap=tk.WORD,
            bg='#2e3440',
            fg='#d8dee9',
            font=('Georgia', 11),
            padx=15,
            pady=15,
            relief='flat'
        )
        help_text.pack(fill=tk.BOTH, expand=True)

        help_content = """
        RPG World Simulator - Мудрость старца

        Добро пожаловать в мир приключений! Здесь вы можете:

        1. Создать героев разных классов
        2. Отправить их в путешествие по миру
        3. Наблюдать за их приключениями

        Управление:

        • Создать героя - добавить одного персонажа
        • Создать отряд - добавить группу персонажей
        • Начать приключение - запустить симуляцию
        • Остановить время - приостановить симуляцию

        Горячие клавиши:
        Ctrl+N - Создать героя
        Ctrl+G - Создать отряд
        F5 - Начать приключение
        F6 - Остановить время
        Ctrl+Q - Выйти из программы
        F1 - Эта справка

        Пусть удача сопутствует вашим героям!
        """

        help_text.insert(tk.END, help_content)
        help_text.config(state=tk.DISABLED)

        # Кнопка закрытия
        ttk.Button(
            help_window,
            text="Понятно",
            command=help_window.destroy,
            style='TButton'
        ).pack(pady=10)

    def show_about(self):
        """Показать информацию о программе"""
        about_window = tk.Toplevel(self.root)
        about_window.title("О программе")
        about_window.geometry("400x300")
        about_window.resizable(False, False)

        # Стилизованное окно "О программе"
        about_text = tk.Text(
            about_window,
            wrap=tk.WORD,
            bg='#2e3440',
            fg='#d8dee9',
            font=('Georgia', 11),
            padx=15,
            pady=15,
            relief='flat'
        )
        about_text.pack(fill=tk.BOTH, expand=True)

        about_content = """
        RPG World Simulator

        Версия: 1.0
        Автор: Таинственный маг

        Эта программа создает мир, населенный героями 
        и монстрами, и позволяет наблюдать за их 
        приключениями.

        Используемые технологии:
        • Python 3
        • Tkinter
        • PIL (для изображений)

        © 2023 Таинственное королевство
        """

        about_text.insert(tk.END, about_content)
        about_text.config(state=tk.DISABLED)

        # Кнопка закрытия
        ttk.Button(
            about_window,
            text="Закрыть",
            command=about_window.destroy,
            style='TButton'
        ).pack(pady=10)

    def add_character(self):
        """Диалог добавления нового персонажа"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Создание героя")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # Фоновый цвет
        dialog.configure(bg='#3b4252')

        # Заголовок
        ttk.Label(
            dialog,
            text="Создание нового героя",
            font=("Papyrus", 14, "bold"),
            foreground="#88c0d0",
            background="#3b4252"
        ).pack(pady=10)

        # Фрейм для формы
        form_frame = ttk.Frame(dialog)
        form_frame.pack(pady=10, padx=20, fill=tk.X)

        # Поле имени
        ttk.Label(
            form_frame,
            text="Имя героя:",
            font=("Georgia", 10),
            background="#3b4252"
        ).grid(row=0, column=0, sticky="w", pady=5)

        name_entry = ttk.Entry(form_frame, font=("Georgia", 10))
        name_entry.grid(row=0, column=1, sticky="ew", pady=5)

        # Выбор класса
        ttk.Label(
            form_frame,
            text="Класс:",
            font=("Georgia", 10),
            background="#3b4252"
        ).grid(row=1, column=0, sticky="w", pady=5)

        class_var = tk.StringVar()
        class_combo = ttk.Combobox(
            form_frame,
            textvariable=class_var,
            values=list(self.classes.keys()),
            font=("Georgia", 10),
            state="readonly"
        )
        class_combo.grid(row=1, column=1, sticky="ew", pady=5)
        class_combo.current(0)

        # Выбор подкласса
        ttk.Label(
            form_frame,
            text="Подкласс:",
            font=("Georgia", 10),
            background="#3b4252"
        ).grid(row=2, column=0, sticky="w", pady=5)

        subclass_var = tk.StringVar()
        subclass_combo = ttk.Combobox(
            form_frame,
            textvariable=subclass_var,
            font=("Georgia", 10),
            state="readonly"
        )
        subclass_combo.grid(row=2, column=1, sticky="ew", pady=5)

        # Обновление подклассов при выборе класса
        def update_subclasses(event=None):
            selected_class = class_var.get()
            if selected_class in self.classes:
                subclasses = self.classes[selected_class]
                subclass_combo["values"] = subclasses
                if subclasses:
                    subclass_combo.current(0)

        class_combo.bind("<<ComboboxSelected>>", update_subclasses)
        update_subclasses()  # Инициализация

        # Кнопки
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)

        def create_hero():
            name = name_entry.get()
            char_class = class_var.get()
            subclass = subclass_var.get()

            if not name:
                messagebox.showerror("Ошибка", "Герой должен иметь имя!", parent=dialog)
                return

            char = self.create_character(char_class, subclass, name)
            self.game_world.add_npc(char)
            self.update_ui()
            dialog.destroy()

        ttk.Button(
            button_frame,
            text="Создать героя",
            command=create_hero,
            style='TButton'
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Отмена",
            command=dialog.destroy,
            style='TButton'
        ).pack(side=tk.LEFT, padx=5)

    def add_multiple_characters(self):
        """Диалог добавления нескольких персонажей"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Создание отряда")
        dialog.geometry("400x350")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # Фоновый цвет
        dialog.configure(bg='#3b4252')

        # Заголовок
        ttk.Label(
            dialog,
            text="Создание отряда",
            font=("Papyrus", 14, "bold"),
            foreground="#88c0d0",
            background="#3b4252"
        ).pack(pady=10)

        # Фрейм для формы
        form_frame = ttk.Frame(dialog)
        form_frame.pack(pady=10, padx=20, fill=tk.X)

        # Количество персонажей
        ttk.Label(
            form_frame,
            text="Число героев:",
            font=("Georgia", 10),
            background="#3b4252"
        ).grid(row=0, column=0, sticky="w", pady=5)

        count_var = tk.IntVar(value=3)
        ttk.Spinbox(
            form_frame,
            from_=1,
            to=10,
            textvariable=count_var,
            font=("Georgia", 10)
        ).grid(row=0, column=1, sticky="ew", pady=5)

        # Префикс имен
        ttk.Label(
            form_frame,
            text="Префикс имен:",
            font=("Georgia", 10),
            background="#3b4252"
        ).grid(row=1, column=0, sticky="w", pady=5)

        prefix_var = tk.StringVar(value="Герой")
        ttk.Entry(
            form_frame,
            textvariable=prefix_var,
            font=("Georgia", 10)
        ).grid(row=1, column=1, sticky="ew", pady=5)

        # Выбор класса
        ttk.Label(
            form_frame,
            text="Основной класс:",
            font=("Georgia", 10),
            background="#3b4252"
        ).grid(row=2, column=0, sticky="w", pady=5)

        class_var = tk.StringVar()
        class_combo = ttk.Combobox(
            form_frame,
            textvariable=class_var,
            values=list(self.classes.keys()),
            font=("Georgia", 10),
            state="readonly"
        )
        class_combo.grid(row=2, column=1, sticky="ew", pady=5)
        class_combo.current(0)

        # Кнопки
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)

        def create_group():
            count = count_var.get()
            prefix = prefix_var.get()
            char_class = class_var.get()

            if not prefix:
                messagebox.showerror("Ошибка", "Укажите префикс имен!", parent=dialog)
                return

            npc_list = []
            for i in range(1, count + 1):
                name = f"{prefix} {i}"
                subclass = random.choice(self.classes[char_class])
                npc_list.append(self.create_character(char_class, subclass, name))

            self.game_world.add_multiple_npcs(npc_list)
            self.update_ui()
            dialog.destroy()

        ttk.Button(
            button_frame,
            text="Создать отряд",
            command=create_group,
            style='TButton'
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Отмена",
            command=dialog.destroy,
            style='TButton'
        ).pack(side=tk.LEFT, padx=5)

    def create_character_display(self, parent, npc):
        """Создание отображения персонажа с иконкой"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)

        # Иконка класса
        class_name = npc.__class__.__bases__[0].__name__
        if class_name not in self.class_images:
            class_name = "Маг"  # Запасной вариант

        icon_label = ttk.Label(frame, image=self.class_images.get(class_name, None))
        icon_label.pack(side=tk.LEFT, padx=5)

        # Информация о персонаже
        info_frame = ttk.Frame(frame)
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(
            info_frame,
            text=f"{npc.name} ({npc.__class__.__name__})",
            font=("Georgia", 10, "bold")
        ).pack(anchor="w")

        ttk.Label(
            info_frame,
            text=f"Ур. {npc.level}, HP: {npc.health}/{npc.max_health}",
            font=("Georgia", 9)
        ).pack(anchor="w")

        ttk.Label(
            info_frame,
            text=f"Состояние: {npc.state}",
            font=("Georgia", 9)
        ).pack(anchor="w")

        return frame

    def create_character(self, class_name, subclass, name):
        """Создание экземпляра персонажа"""
        class_map = {
            "Маг": {
                "Архимаг": Archmage,
                "Некромант": Necromancer
            },
            "Воин": {
                "Берсерк": Berserker,
                "Паладин": Paladin
            },
            "Разбойник": {
                "Ассасин": Assassin,
                "Теневой плясун": Shadowdancer
            },
            "Жрец": {
                "Инквизитор": Inquisitor,
                "Друид": Druid
            },
            "Лучник": {
                "Снайпер": Sniper,
                "Рейнджер": Ranger
            },
            "Алхимик": {
                "Бомбардир": Bomber,
                "Трансмутатор": Transmuter
            }
        }
        return class_map[class_name][subclass](name)

    def start_simulation(self):
        """Запуск симуляции"""
        if not self.game_world.npcs:
            messagebox.showwarning(
                "Нет героев",
                "Добавьте хотя бы одного героя перед началом приключения!",
                parent=self.root
            )
            return

        if not self.game_world.is_running:
            self.game_world.start_simulation()
            self.simulation_thread = threading.Thread(
                target=self.run_simulation,
                daemon=True
            )
            self.simulation_thread.start()
            self.update_ui()

    def stop_simulation(self):
        """Остановка симуляции"""
        if self.game_world.is_running:
            self.game_world.stop_simulation()
            self.update_ui()

    def run_simulation(self):
        """Основной цикл симуляции"""
        while self.game_world.is_running:
            self.game_world.simulate_turn()
            self.root.after(100, self.update_ui)
            time.sleep(1.0 / self.game_world.simulation_speed)

    def determine_log_color(self, message):
        """Определение цвета сообщения в логе"""
        message_lower = message.lower()

        if any(word in message_lower for word in ["повержен", "умирает", "погиб"]):
            return "death"
        elif any(word in message_lower for word in ["атакует", "урон", "бьёт", "поражает"]):
            return "combat"
        elif any(word in message_lower for word in ["исцеляет", "восстанавливает", "регенерация"]):
            return "heal"
        elif any(word in message_lower for word in ["находит", "золота", "артефакт"]):
            return "loot"
        elif any(word in message_lower for word in ["уровень", "опыта", "достигает"]):
            return "level"
        elif any(word in message_lower for word in ["заклинание", "кастует", "магический"]):
            return "spell"
        elif any(word in message_lower for word in ["эффект", "отравлен", "заморожен", "горит"]):
            return "status"
        elif any(word in message_lower for word in ["монстр", "дракон", "гоблин", "тролль"]):
            return "monster"
        elif message.startswith("==="):
            return "system"
        else:
            return "default"

    def update_ui(self):
        """Обновление интерфейса"""
        # Обновление лога событий
        self.log_text.config(state=tk.NORMAL)

        # Добавляем только новые события
        current_log_length = len(self.game_world.event_log)
        prev_log_length = getattr(self, 'prev_log_length', 0)

        if current_log_length > prev_log_length:
            new_events = self.game_world.event_log[prev_log_length:]
            for event in new_events:
                color_tag = self.determine_log_color(event)
                self.log_text.insert(tk.END, event + "\n", color_tag)

            self.log_text.see(tk.END)
            self.prev_log_length = current_log_length

        self.log_text.config(state=tk.DISABLED)

        # Обновление статистики
        stats = self.game_world.get_stats()

        # Общая статистика
        self.turn_label.config(text=f"Ход: {stats['turn_count']}")
        self.locations_label.config(text=f"Локации: {stats['locations']}")
        self.monsters_label.config(text=f"Монстры: {stats['alive_monsters']}")

        # Очистка предыдущих героев
        for widget in self.heroes_frame.winfo_children():
            widget.destroy()

            # Добавление текущих героев с иконками
        self.heroes_label.config(text=f"Герои ({len(stats['alive_npcs'])})")

        for npc in stats['alive_npcs']:
            self.create_character_display(self.heroes_frame, npc)

        # Добавление текущих героев
        self.heroes_label.config(text=f"Герои ({len(stats['alive_npcs'])})")

        for npc in stats['alive_npcs']:
            char_frame = ttk.Frame(self.heroes_frame)
            char_frame.pack(fill=tk.X, pady=5)

            # Иконка класса
            class_icon = ttk.Label(char_frame, text="⚔", font=("Arial", 14))
            class_icon.pack(side=tk.LEFT, padx=5)

            # Информация о персонаже
            info_frame = ttk.Frame(char_frame)
            info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

            ttk.Label(
                info_frame,
                text=f"{npc.name} ({npc.__class__.__name__})",
                font=("Georgia", 10, "bold")
            ).pack(anchor="w")

            ttk.Label(
                info_frame,
                text=f"Ур. {npc.level}, HP: {npc.health}/{npc.max_health}",
                font=("Georgia", 9)
            ).pack(anchor="w")

            ttk.Label(
                info_frame,
                text=f"Состояние: {npc.state}",
                font=("Georgia", 9)
            ).pack(anchor="w")

            # Разделитель
            ttk.Separator(char_frame).pack(fill=tk.X, pady=2)

        # Очистка предыдущих погибших
        for widget in self.dead_heroes_frame.winfo_children():
            widget.destroy()

        # Добавление погибших героев
        self.dead_label.config(text=f"Погибшие ({len(stats['dead_npcs'])})")

        for npc in stats['dead_npcs'][:5]:  # Показываем только первых 5
            ttk.Label(
                self.dead_heroes_frame,
                text=f"{npc.name} (ур. {npc.level})",
                font=("Georgia", 9),
                foreground="#bf616a"
            ).pack(anchor="w")

        if len(stats['dead_npcs']) > 5:
            ttk.Label(
                self.dead_heroes_frame,
                text=f"... и еще {len(stats['dead_npcs']) - 5}",
                font=("Georgia", 8),
                foreground="#bf616a"
            ).pack(anchor="w")

        # Обновление состояния кнопок
        running = self.game_world.is_running
        self.start_btn.config(state=tk.DISABLED if running else tk.NORMAL)
        self.stop_btn.config(state=tk.NORMAL if running else tk.DISABLED)
        self.add_btn.config(state=tk.DISABLED if running else tk.NORMAL)
        self.add_multiple_btn.config(state=tk.DISABLED if running else tk.NORMAL)


if __name__ == "__main__":
    root = tk.Tk()
    app = GameGUI(root)
    root.mainloop()