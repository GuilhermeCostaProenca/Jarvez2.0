"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Races = void 0;
const Dahllan_1 = require("./Dahllan/Dahllan");
const Dwarf_1 = require("./Dwarf");
const Elf_1 = require("./Elf");
const Goblin_1 = require("./Goblin/");
const Human_1 = require("./Human");
const Lefeu_1 = require("./Lefeu/Lefeu");
const Minotaur_1 = require("./Minotaur");
const Qareen_1 = require("./Qareen/Qareen");
class Races {
    static getAll() {
        return Object.values(Races.map);
    }
    static getByName(name) {
        return Races.map[name];
    }
}
exports.Races = Races;
Races.map = {
    dwarf: Dwarf_1.Dwarf,
    human: Human_1.Human,
    dahllan: Dahllan_1.Dahllan,
    elf: Elf_1.Elf,
    goblin: Goblin_1.Goblin,
    lefeu: Lefeu_1.Lefeu,
    minotaur: Minotaur_1.Minotaur,
    qareen: Qareen_1.Qareen,
};
