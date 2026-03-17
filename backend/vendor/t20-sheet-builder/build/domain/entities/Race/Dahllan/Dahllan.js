"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Dahllan = void 0;
const WildEmpathy_1 = require("../../Ability/common/WildEmpathy");
const Race_1 = require("../Race");
const RaceName_1 = require("../RaceName");
const AllihannaArmor_1 = require("./AllihannaArmor");
const PlantsFriend_1 = require("./PlantsFriend");
class Dahllan extends Race_1.Race {
    constructor() {
        super(Dahllan.raceName);
        this.attributeModifiers = Dahllan.attributeModifiers;
        this.abilities = {
            plantsFriend: new PlantsFriend_1.PlantsFriend(),
            allihannaArmor: new AllihannaArmor_1.AllihannaArmor(),
            wildEmpathy: new WildEmpathy_1.WildEmpathy(),
        };
    }
    serializeSpecific() {
        return {
            name: Dahllan.raceName,
        };
    }
}
exports.Dahllan = Dahllan;
Dahllan.attributeModifiers = {
    wisdom: 2,
    dexterity: 1,
    intelligence: -1,
};
Dahllan.raceName = RaceName_1.RaceName.dahllan;
