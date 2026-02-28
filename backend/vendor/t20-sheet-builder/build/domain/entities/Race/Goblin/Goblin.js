"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Goblin = void 0;
const Race_1 = require("../Race");
const RaceName_1 = require("../RaceName");
const Ingenious_1 = require("./Ingenious");
const Jointer_1 = require("./Jointer");
const SlenderPlage_1 = require("./SlenderPlage");
const StreetRat_1 = require("./StreetRat");
class Goblin extends Race_1.Race {
    constructor() {
        super(RaceName_1.RaceName.goblin);
        this.attributeModifiers = Goblin.attributeModifiers;
        this.abilities = Goblin.abilities;
    }
    serializeSpecific() {
        return {
            name: Goblin.raceName,
        };
    }
}
exports.Goblin = Goblin;
Goblin.raceName = RaceName_1.RaceName.goblin;
Goblin.attributeModifiers = {
    charisma: -1,
    dexterity: 2,
    intelligence: 1,
};
Goblin.abilities = {
    ingenious: new Ingenious_1.Ingenious(),
    jointer: new Jointer_1.Jointer(),
    slenderPlage: new SlenderPlage_1.SlenderPlage(),
    streetRat: new StreetRat_1.StreetRat(),
};
