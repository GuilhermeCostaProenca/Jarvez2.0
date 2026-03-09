"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.RaceFactory = void 0;
const errors_1 = require("../../errors");
const Dahllan_1 = require("./Dahllan/Dahllan");
const Dwarf_1 = require("./Dwarf");
const Elf_1 = require("./Elf");
const Goblin_1 = require("./Goblin");
const Human_1 = require("./Human");
const Lefeu_1 = require("./Lefeu");
const Minotaur_1 = require("./Minotaur");
const Qareen_1 = require("./Qareen");
const RaceName_1 = require("./RaceName");
class RaceFactory {
    static makeFromSerialized(serializedRace) {
        switch (serializedRace.name) {
            case RaceName_1.RaceName.human:
                return RaceFactory.makeHuman(serializedRace);
            case RaceName_1.RaceName.dwarf:
                return RaceFactory.makeDwarf(serializedRace);
            case RaceName_1.RaceName.dahllan:
                return RaceFactory.makeDahllan(serializedRace);
            case RaceName_1.RaceName.elf:
                return RaceFactory.makeElf(serializedRace);
            case RaceName_1.RaceName.goblin:
                return RaceFactory.makeGoblin(serializedRace);
            case RaceName_1.RaceName.lefeu:
                return RaceFactory.makeLefeu(serializedRace);
            case RaceName_1.RaceName.minotaur:
                return RaceFactory.makeMinotaur(serializedRace);
            case RaceName_1.RaceName.qareen:
                return RaceFactory.makeQareen(serializedRace);
            default:
                throw new errors_1.SheetBuilderError('UNKNOWN_RACE');
        }
    }
    static makeHuman(serializedRace) {
        const choices = serializedRace.versatileChoices.map(choice => Human_1.VersatileChoiceFactory.make(choice.type, choice.name));
        return new Human_1.Human(serializedRace.selectedAttributes, choices);
    }
    static makeMinotaur(_serializedRace) {
        return new Minotaur_1.Minotaur();
    }
    static makeQareen(serializedRace) {
        return new Qareen_1.Qareen(serializedRace.qareenType, serializedRace.mysticTattooSpell);
    }
    static makeElf(_serializedRace) {
        return new Elf_1.Elf();
    }
    static makeGoblin(_serializedRace) {
        return new Goblin_1.Goblin();
    }
    static makeDwarf(_serializedRace) {
        return new Dwarf_1.Dwarf();
    }
    static makeDahllan(_serializedRace) {
        return new Dahllan_1.Dahllan();
    }
    static makeLefeu(serialized) {
        const lefeu = new Lefeu_1.Lefeu(serialized.selectedAttributes);
        lefeu.addDeformities(serialized.deformityChoices.map(choice => choice.name));
        lefeu.setPreviousRace(serialized.previousRace);
        return lefeu;
    }
}
exports.RaceFactory = RaceFactory;
