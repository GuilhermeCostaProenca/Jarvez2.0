"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ControlPlants = void 0;
const Spell_1 = require("../Spell");
const SpellCircle_1 = require("../SpellCircle");
const SpellName_1 = require("../SpellName");
const SpellSchool_1 = require("../SpellSchool");
const Ability_1 = require("../../Ability");
const ControlPlantsDefaultEffect_1 = require("./ControlPlantsDefaultEffect");
class ControlPlants extends Spell_1.Spell {
    static get shortDescription() {
        return 'Vegetação enreda criaturas.';
    }
    constructor() {
        super(ControlPlants.spellName, ControlPlants.circle, 'arcane');
        this.school = ControlPlants.school;
        this.shortDescription = ControlPlants.shortDescription;
        this.effects = new Ability_1.AbilityEffects({
            activateable: {
                default: new ControlPlantsDefaultEffect_1.ControlPlantsDefaultEffect(),
            },
        });
    }
}
exports.ControlPlants = ControlPlants;
ControlPlants.circle = SpellCircle_1.SpellCircle.first;
ControlPlants.school = SpellSchool_1.SpellSchool.transmutation;
ControlPlants.spellName = SpellName_1.SpellName.controlPlants;
ControlPlants.spellType = 'arcane';
