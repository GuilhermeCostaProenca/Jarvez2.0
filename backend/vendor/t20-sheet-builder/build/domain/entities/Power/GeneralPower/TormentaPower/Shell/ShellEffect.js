"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ShellEffect = void 0;
const PassiveEffect_1 = require("../../../../Ability/PassiveEffect");
const AddFixedModifierToDefense_1 = require("../../../../Action/AddFixedModifierToDefense");
const FixedModifier_1 = require("../../../../Modifier/FixedModifier/FixedModifier");
const GeneralPowerName_1 = require("../../GeneralPowerName");
class ShellEffect extends PassiveEffect_1.PassiveEffect {
    get description() {
        return ShellEffect.description;
    }
    constructor() {
        super(GeneralPowerName_1.GeneralPowerName.shell);
    }
    apply(transaction) {
        transaction.run(new AddFixedModifierToDefense_1.AddFixedModifierToDefense({
            payload: {
                modifier: new FixedModifier_1.FixedModifier(GeneralPowerName_1.GeneralPowerName.shell, 1),
            },
            transaction,
        }));
    }
}
exports.ShellEffect = ShellEffect;
ShellEffect.description = 'Sua pele é recoberta por placas quitinosas. Você recebe +1 na Defesa.';
