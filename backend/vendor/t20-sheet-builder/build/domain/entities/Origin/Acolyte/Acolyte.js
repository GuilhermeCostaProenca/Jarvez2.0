"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Acolyte = void 0;
const EquipmentAdventure_1 = require("../../Inventory/Equipment/EquipmentAdventure/EquipmentAdventure");
const EquipmentClothing_1 = require("../../Inventory/Equipment/EquipmentClothing/EquipmentClothing");
const EquipmentName_1 = require("../../Inventory/Equipment/EquipmentName");
const GeneralPowerName_1 = require("../../Power/GeneralPower/GeneralPowerName");
const OriginPowerName_1 = require("../../Power/OriginPower/OriginPowerName");
const SkillName_1 = require("../../Skill/SkillName");
const Origin_1 = require("../Origin");
const OriginName_1 = require("../OriginName");
class Acolyte extends Origin_1.Origin {
    constructor(chosenBenefits) {
        super(chosenBenefits, {
            skills: Acolyte.skills,
            generalPowers: Acolyte.generalPowers,
            originPower: Acolyte.originPower,
        });
        this.name = Acolyte.originName;
        this.equipments = [
            new EquipmentAdventure_1.EquipmentAdventure(EquipmentName_1.EquipmentName.sacredSymbol),
            new EquipmentClothing_1.EquipmentClothing(EquipmentName_1.EquipmentName.priestCostume),
        ];
    }
    serialize() {
        return {
            name: this.name,
            chosenBenefits: this.serializeBenefits(),
            equipments: this.serializeEquipments(),
        };
    }
}
exports.Acolyte = Acolyte;
Acolyte.originName = OriginName_1.OriginName.acolyte;
Acolyte.equipments = 'Símbolo sagrado, traje de sacerdote.';
Acolyte.skills = [SkillName_1.SkillName.cure, SkillName_1.SkillName.religion, SkillName_1.SkillName.will];
Acolyte.generalPowers = [GeneralPowerName_1.GeneralPowerName.medicine, GeneralPowerName_1.GeneralPowerName.ironWill];
Acolyte.originPower = OriginPowerName_1.OriginPowerName.churchMember;
