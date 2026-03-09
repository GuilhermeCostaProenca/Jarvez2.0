"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ElementalResistance = void 0;
const Ability_1 = require("../../../Ability");
const ResistanceName_1 = require("../../../Resistance/ResistanceName");
const RaceAbility_1 = require("../../RaceAbility");
const RaceAbilityName_1 = require("../../RaceAbilityName");
const ElementalResistanceEffect_1 = require("./ElementalResistanceEffect");
class ElementalResistance extends RaceAbility_1.RaceAbility {
    constructor(qareenType) {
        super(RaceAbilityName_1.RaceAbilityName.elementalResistance);
        this.effects = new Ability_1.AbilityEffects({
            passive: {
                default: new ElementalResistanceEffect_1.ElementalResistanceEffect(ElementalResistance.qareenTypeToResistance[qareenType]),
            },
        });
    }
}
exports.ElementalResistance = ElementalResistance;
ElementalResistance.qareenTypeToResistance = {
    air: ResistanceName_1.ResistanceName.electricity,
    darkness: ResistanceName_1.ResistanceName.darkness,
    earth: ResistanceName_1.ResistanceName.acid,
    fire: ResistanceName_1.ResistanceName.fire,
    light: ResistanceName_1.ResistanceName.light,
    water: ResistanceName_1.ResistanceName.cold,
};
