"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Dwarf = void 0;
const Race_1 = require("../Race");
const RaceName_1 = require("../RaceName");
const HardAsRock_1 = require("./HardAsRock/HardAsRock");
const HeredrimmTradition_1 = require("./HeredrimmTradition/HeredrimmTradition");
const RockKnowledge_1 = require("./RockKnowledge/RockKnowledge");
const SlowAndAlways_1 = require("./SlowAndAlways/SlowAndAlways");
class Dwarf extends Race_1.Race {
    constructor() {
        super(RaceName_1.RaceName.dwarf);
        this.abilities = {
            rockKnowledge: new RockKnowledge_1.RockKnowledge(),
            slowAndAlways: new SlowAndAlways_1.SlowAndAlways(),
            hardAsRock: new HardAsRock_1.HardAsRock(),
            heredrimmTradition: new HeredrimmTradition_1.HeredrimmTradition(),
        };
        this.attributeModifiers = Dwarf.attributeModifiers;
    }
    serializeSpecific() {
        return {
            name: Dwarf.raceName,
        };
    }
}
exports.Dwarf = Dwarf;
Dwarf.raceName = RaceName_1.RaceName.dwarf;
Dwarf.attributeModifiers = {
    dexterity: -1,
    constitution: 2,
    wisdom: 1,
};
