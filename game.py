class NPC:
    def __init__(self, name):
        self.name = name

class Mage(NPC):
    def join_party(self):
        return f"К партии присоединяется маг {self.name}."
    def cast_spell(self, spell, target=None):
        return f"{self.name} читает заклинание: {spell}." + (f" {target.name} замерзает на месте." if target else "")
    def speak(self, message):
        return f"{self.name} говорит: \"{message}\""

class Rogue(NPC):
    def sneak(self):
        return f"{self.name} крадётся в тени."
    def backstab(self, target, damage):
        return f"{self.name} наносит удар в спину: -{damage} НР {target.name}."
    def disable_trap(self):
        return f"{self.name} обезвреживает ловушку."

class Orc(NPC):
    def take_damage(self, attacker):
        return f"{self.name} получает удар от {attacker.name}."
    def growl(self, message):
        return f"{self.name} рычит: \"{message}\""

class Paladin(NPC):
    def exclaim(self, message):
        return f"{self.name} восклицает: \"{message}\""

class Warrior(NPC):
    def throw_axe(self):
        return f"{self.name} бросает топор: критический удар!"
    def pick_up_item(self, item):
        return f"{self.name} подбирает предмет: {item}."

class Druid(NPC):
    def join_party(self):
        return f"К партии присоединяется друид {self.name}."
    def summon_spirit_wolf(self):
        return f"{self.name} призывает волка-духа."

class SpiritWolf(NPC):
    def bite(self, target, damage):
        return f"Волк-дух кусает {target.name}: -{damage} НР."

class Zombie(NPC):
    def die(self):
        return f"{self.name} падает замертво."

class Skeleton(NPC):
    def crumble(self):
        return f"{self.name} разрушается."

class Vampire(NPC):
    def transform_to_bat(self):
        return f"{self.name} обращается в летучую мышь."

class Human(NPC):
    def use_potion(self, potion, effect):
        return f"{self.name} использует: {potion}. {self.name} {effect}."

class Elf(NPC):
    def cast_fireball(self, target, damage):
        return f"{self.name} кастует: Огненный шар. {target.name} получает {damage} урона."
    def pick_up_item(self, item):
        return f"{self.name} находит: {item}."

class Dwarf(NPC):
    def shout(self, message):
        return f"{self.name} кричит: \"{message}\""
    def break_item(self, item):
        return f"{self.name} ломает: {item}."

# Создание NPC
elrin = Mage("Элрин23")
shaira = Rogue("Шайра17")
grog = Orc("Грогнак99")
lianor = Paladin("Лианор10")
murk = NPC("Мурк5")
torbr = Warrior("Торбранд77")
elisa = Druid("Элиса31")
spirit_wolf = SpiritWolf("Волк-дух")
ratch = Zombie("Рэтч6")
alister = Mage("Алистер8")
grash = Orc("Грашак23")
dorian = Human("Дориан5")
tiandra = Elf("Тиандра17")
torin = Dwarf("Торин91")
mordred = Vampire("Мордред66")
skeleton_warrior = Skeleton("Скелет Воина")
skeleton44 = Skeleton("Костяшка44")

# Генерация лога
log = [
    elrin.join_party(),
    shaira.sneak(),
    grog.take_damage(lianor),
    lianor.exclaim("Свет ведёт нас!"),
    elrin.cast_spell("Оковы Льда", murk),
    f"{murk.name} замерзает на месте.",
    shaira.backstab(murk, 12),
    grog.growl("Вы заплатите за это!"),
    torbr.throw_axe(),
    f"{skeleton_warrior.name} разваливается на кости.",
    elisa.join_party(),
    elisa.summon_spirit_wolf(),
    spirit_wolf.bite(ratch, 9),
    ratch.die(),
    torbr.pick_up_item("Щит Упорства"),
    shaira.disable_trap(),
    elrin.speak("Нам нужно отдохнуть."),
    f"{alister.name} входит в подземелье.",
    f"{grash.name} атакует: {dorian.name}.",
    f"{dorian.name} теряет 12 здоровья.",
    tiandra.cast_fireball(grash, 24),
    torin.shout("За сокровища предков!"),
    tiandra.pick_up_item("Свиток телепортации"),
    skeleton44.crumble(),
    f"{alister.name} получает: 120 опыта.",
    torin.break_item("Ржавый замок"),
    mordred.transform_to_bat(),
    dorian.use_potion("Зелье лечения", "восстанавливает 15 здоровья.")
]

# Вывод лога
for entry in log:
    print(entry)