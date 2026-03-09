"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Qareen = void 0;
const Race_1 = require("../Race");
const RaceName_1 = require("../RaceName");
const Desires_1 = require("./Desires/Desires");
const ElementalResistance_1 = require("./ElementalResistance/ElementalResistance");
const MysticTattoo_1 = require("./MysticTattoo/MysticTattoo");
class Qareen extends Race_1.Race {
    constructor(qareenType, mysticTattooSpell) {
        super(Qareen.raceName);
        this.qareenType = qareenType;
        this.attributeModifiers = Qareen.attributeModifiers;
        this.abilities = {
            desires: new Desires_1.Desires(),
            elementalResistance: new ElementalResistance_1.ElementalResistance(this.qareenType),
            mysticTattoo: new MysticTattoo_1.MysticTattoo(mysticTattooSpell),
        };
    }
    serializeSpecific() {
        return {
            name: Qareen.raceName,
            mysticTattooSpell: this.abilities.mysticTattoo.spell,
            qareenType: this.qareenType,
        };
    }
}
exports.Qareen = Qareen;
Qareen.attributeModifiers = {
    charisma: 2,
    intelligence: 1,
    wisdom: -1,
};
Qareen.raceName = RaceName_1.RaceName.qareen;
