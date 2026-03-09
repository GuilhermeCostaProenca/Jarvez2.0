"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AddFixedModifierToSkill = void 0;
const Modifier_1 = require("../Modifier");
const ModifierValue_1 = require("../Modifier/ModifierValue");
const Translatable_1 = require("../Translatable");
const Action_1 = require("./Action");
class AddFixedModifierToSkill extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'addFixedModifierToSkill' }));
    }
    execute() {
        const sheetSkills = this.transaction.sheet.getSheetSkills();
        sheetSkills.addFixedModifierTo(this.payload.skill, this.payload.modifier);
    }
    getDescription() {
        const skill = new Translatable_1.Translatable(this.payload.skill).getTranslation();
        const source = new Translatable_1.Translatable(this.payload.modifier.source).getTranslation();
        const attributes = this.transaction.sheet.getSheetAttributes().getValues();
        const calculator = new Modifier_1.FixedModifierAppliableValueCalculator(attributes);
        const value = this.payload.modifier.getAppliableValue(calculator);
        const valueWithSign = new ModifierValue_1.ModifierValue(value).getValueWithSign();
        return `${source}: ${valueWithSign} ${skill} aplicado.`;
    }
}
exports.AddFixedModifierToSkill = AddFixedModifierToSkill;
