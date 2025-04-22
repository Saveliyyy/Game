from abc import ABC, abstractmethod


class NPC(ABC):
    def __init__(self, name):
        self.name = name
        self.health = 100
        self.level = 1
        self.experience = 0
        self.inventory = []
        self.status_effects = []

    @abstractmethod
    def join_party(self):
        pass

    def gain_exp(self, amount):
        self.experience += amount
        if self.experience >= 100 * self.level:
            self.level_up()

    def level_up(self):
        self.level += 1
        self.experience = 0
        return f"{self.name} достигает {self.level} уровня!"


# Добавляем недостающий миксин
class SpellcasterMixin:
    def cast_spell(self, spell_name, target=None):
        message = f"{self.name} читает заклинание: {spell_name}"
        if target:
            message += f". {target.name} замерзает на месте."
        return message


class CombatMixin:
    def take_damage(self, damage, attacker=None):
        self.health = max(0, self.health - damage)
        if attacker:
            return f"{self.name} получает {damage} урона от {attacker.name}."
        return f"{self.name} теряет {damage} здоровья."


class Mage(NPC, SpellcasterMixin):  # Теперь миксин определён
    def join_party(self):
        return f"К партии присоединяется маг {self.name}."

    def learn_spell(self, spell_name):
        if self.level >= 3 and spell_name not in self.known_spells:
            self.known_spells.append(spell_name)
            return f"{self.name} изучает: {spell_name}!"
        return "Недостаточно уровня"


# Пример использования
elrin = Mage("Элрин23")
print(elrin.join_party())  # К партии присоединяется маг Элрин23
print(elrin.cast_spell("Ледяная стрела"))  # Элрин23 читает заклинание: Ледяная стрела