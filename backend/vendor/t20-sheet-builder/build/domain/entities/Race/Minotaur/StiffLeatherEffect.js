"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.StiffLeatherEffect = void 0;
const Ability_1 = require("../../Ability");
const AddFixedModifierToDefense_1 = require("../../Action/AddFixedModifierToDefense");
const Modifier_1 = require("../../Modifier");
const RaceAbilityName_1 = require("../RaceAbilityName");
class StiffLeatherEffect extends Ability_1.PassiveEffect {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.stiffLeather);
        this.description = 'Sua pele é dura como a de um '
            + 'touro. Você recebe +1 na Defesa.';
    }
    apply(transaction) {
        const modifier = new Modifier_1.FixedModifier(this.source, 1);
        transaction.run(new AddFixedModifierToDefense_1.AddFixedModifierToDefense({ payload: { modifier }, transaction }));
    }
}
exports.StiffLeatherEffect = StiffLeatherEffect;
