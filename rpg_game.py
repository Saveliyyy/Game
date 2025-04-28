import tkinter as tk
from logging import root
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
        self.root.title("RPG World Simulator")
        self.game_world = GameWorld()
        self.simulation_thread = None

        self.classes = {
            "Маг": ["Архимаг", "Некромант"],
            "Воин": ["Берсерк", "Паладин"],
            "Разбойник": ["Ассасин", "Теневой плясун"],
            "Жрец": ["Инквизитор", "Друид"],
            "Лучник": ["Снайпер", "Рейнджер"],
            "Алхимик": ["Бомбардир", "Трансмутатор"]
        }

        self.create_widgets()
        self.update_ui()

    def create_widgets(self):
        # Основные фреймы
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Панель управления
        control_frame = ttk.LabelFrame(main_frame, text="Управление")
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        # Кнопки управления
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X)

        self.add_btn = ttk.Button(button_frame, text="Добавить персонажа", command=self.add_character)
        self.add_btn.pack(side=tk.LEFT, padx=2)

        self.add_multiple_btn = ttk.Button(button_frame, text="Создать группу", command=self.add_multiple_characters)
        self.add_multiple_btn.pack(side=tk.LEFT, padx=2)

        self.start_btn = ttk.Button(button_frame, text="Старт", command=self.start_simulation)
        self.start_btn.pack(side=tk.LEFT, padx=2)

        self.stop_btn = ttk.Button(button_frame, text="Стоп", command=self.stop_simulation)
        self.stop_btn.pack(side=tk.LEFT, padx=2)

        # Настройки скорости
        speed_frame = ttk.Frame(control_frame)
        speed_frame.pack(fill=tk.X, pady=5)

        ttk.Label(speed_frame, text="Скорость:").pack(side=tk.LEFT)
        self.speed_var = tk.DoubleVar(value=1.0)
        self.speed_scale = ttk.Scale(speed_frame, from_=0.1, to=5.0, variable=self.speed_var,
                                     command=lambda e: self.update_simulation_speed())
        self.speed_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.speed_label = ttk.Label(speed_frame, text="1.0x")
        self.speed_label.pack(side=tk.LEFT)

        # Лог событий и статистика
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.BOTH, expand=True)

        # Лог событий
        log_frame = ttk.LabelFrame(info_frame, text="Лог событий")
        log_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, width=60, height=25)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Статистика
        stats_frame = ttk.LabelFrame(info_frame, text="Статистика", width=300)
        stats_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

        self.stats_text = tk.Text(stats_frame, width=40, height=25)
        self.stats_text.pack(fill=tk.BOTH, expand=True)

    def update_simulation_speed(self):
        speed = self.speed_var.get()
        self.game_world.simulation_speed = speed
        self.speed_label.config(text=f"{speed:.1f}x")

    def add_character(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Создание персонажа")

        # Поля ввода
        ttk.Label(dialog, text="Имя:").grid(row=0, column=0, padx=5, pady=5)
        name_entry = ttk.Entry(dialog)
        name_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(dialog, text="Класс:").grid(row=1, column=0, padx=5, pady=5)
        class_var = tk.StringVar()
        class_combo = ttk.Combobox(dialog, textvariable=class_var, values=list(self.classes.keys()))
        class_combo.grid(row=1, column=1, padx=5, pady=5)
        class_combo.current(0)

        ttk.Label(dialog, text="Подкласс:").grid(row=2, column=0, padx=5, pady=5)
        subclass_var = tk.StringVar()
        subclass_combo = ttk.Combobox(dialog, textvariable=subclass_var)
        subclass_combo.grid(row=2, column=1, padx=5, pady=5)

        def update_subclasses(event):
            subclasses = self.classes.get(class_var.get(), [])
            subclass_combo["values"] = subclasses
            if subclasses:
                subclass_combo.current(0)

        class_combo.bind("<<ComboboxSelected>>", update_subclasses)
        update_subclasses(None)

        def create():
            name = name_entry.get()
            class_name = class_var.get()
            subclass = subclass_var.get()

            if not name:
                messagebox.showerror("Ошибка", "Введите имя персонажа")
                return

            char = self.create_character(class_name, subclass, name)
            self.game_world.add_npc(char)
            self.update_ui()
            dialog.destroy()

        ttk.Button(dialog, text="Создать", command=create).grid(row=3, column=0, columnspan=2, pady=5)

    def create_character(self, class_name, subclass, name):
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

    def add_multiple_characters(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Создание группы персонажей")

        # Количество персонажей
        ttk.Label(dialog, text="Количество персонажей:").grid(row=0, column=0, padx=5, pady=5)
        count_var = tk.IntVar(value=3)
        ttk.Spinbox(dialog, from_=1, to=10, textvariable=count_var).grid(row=0, column=1, padx=5, pady=5)

        # Префикс имен
        ttk.Label(dialog, text="Префикс имен:").grid(row=1, column=0, padx=5, pady=5)
        prefix_var = tk.StringVar(value="Персонаж")
        ttk.Entry(dialog, textvariable=prefix_var).grid(row=1, column=1, padx=5, pady=5)

        # Выбор класса
        ttk.Label(dialog, text="Основной класс:").grid(row=2, column=0, padx=5, pady=5)
        class_var = tk.StringVar()
        class_combo = ttk.Combobox(dialog, textvariable=class_var, values=list(self.classes.keys()))
        class_combo.grid(row=2, column=1, padx=5, pady=5)
        class_combo.current(0)

        def create():
            count = count_var.get()
            prefix = prefix_var.get()
            class_name = class_var.get()

            if not prefix:
                messagebox.showerror("Ошибка", "Введите префикс имен")
                return

            npc_list = []
            for i in range(1, count + 1):
                name = f"{prefix} {i}"
                subclass = random.choice(self.classes[class_name])
                npc_list.append(self.create_character(class_name, subclass, name))

            self.game_world.add_multiple_npcs(npc_list)
            self.update_ui()
            dialog.destroy()

        ttk.Button(dialog, text="Создать группу", command=create).grid(row=3, column=0, columnspan=2, pady=5)

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
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        for event in self.game_world.event_log[-100:]:  # Показываем последние 100 событий
            self.log_text.insert(tk.END, event + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

        # Обновление статистики
        stats = self.game_world.get_stats()
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)

        self.stats_text.insert(tk.END, f"=== ОБЩАЯ СТАТИСТИКА ===\n")
        self.stats_text.insert(tk.END, f"Ход: {stats['turn_count']}\n")
        self.stats_text.insert(tk.END, f"Локации: {stats['locations']}\n")
        self.stats_text.insert(tk.END, f"Монстров: {stats['alive_monsters']}\n\n")

        self.stats_text.insert(tk.END, f'=== ПЕРСОНАЖИ ({len(stats["alive_npcs"])} ===\n')
        for npc in stats['alive_npcs']:
            self.stats_text.insert(tk.END,
                                   f"{npc.name} ({npc.__class__.__name__})\n"
                                   f"Ур. {npc.level}, HP: {npc.health}/{npc.max_health}\n"
                                   f"Состояние: {npc.state}\n\n")

        self.stats_text.insert(tk.END, f"\n=== ПОГИБШИЕ ({len(stats['dead_npcs'])} ===\n")
        for npc in stats['dead_npcs'][:5]:  # Показываем только последних 5
            self.stats_text.insert(tk.END, f"{npc.name} (ур. {npc.level})\n")

        if len(stats['dead_npcs']) > 5:
            self.stats_text.insert(tk.END, f"... и еще {len(stats['dead_npcs']) - 5}\n")

        self.stats_text.config(state=tk.DISABLED)

        # Обновление состояния кнопок
        running = self.game_world.is_running
        self.start_btn.state(["disabled" if running else "!disabled"])
        self.stop_btn.state(["disabled" if not running else "!disabled"])
        self.add_btn.state(["disabled" if running else "!disabled"])
        self.add_multiple_btn.state(["disabled" if running else "!disabled"])


if __name__ == "__main__":
    root = tk.Tk()
    app = GameGUI(root)
    root.mainloop()
