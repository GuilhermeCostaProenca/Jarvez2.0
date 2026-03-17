"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Elf = void 0;
const Race_1 = require("../Race");
const RaceName_1 = require("../RaceName");
const ElvenSenses_1 = require("./ElvenSenses");
const GloriennGrace_1 = require("./GloriennGrace");
const MagicBlood_1 = require("./MagicBlood");
class Elf extends Race_1.Race {
    constructor() {
        super(RaceName_1.RaceName.elf);
        this.attributeModifiers = Elf.attributeModifiers;
        this.abilities = {
            gloriennGrace: new GloriennGrace_1.GloriennGrace(),
            magicBlood: new MagicBlood_1.MagicBlood(),
            elvenSenses: new ElvenSenses_1.ElvenSenses(),
        };
    }
    serializeSpecific() {
        return {
            name: Elf.raceName,
        };
    }
}
exports.Elf = Elf;
Elf.attributeModifiers = {
    intelligence: 2,
    dexterity: 1,
    constitution: -1,
};
Elf.raceName = RaceName_1.RaceName.elf;
