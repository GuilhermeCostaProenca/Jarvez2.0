"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AddFixedModifierToManaPoints = void 0;
const Modifier_1 = require("../Modifier");
const ModifierValue_1 = require("../Modifier/ModifierValue");
const Translatable_1 = require("../Translatable");
const Action_1 = require("./Action");
class AddFixedModifierToManaPoints extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'addFixedModifierToManaPoints' }));
    }
    execute() {
        const sheetManaPoints = this.transaction.sheet.getSheetManaPoints();
        sheetManaPoints.addFixedModifier(this.payload.modifier);
    }
    getDescription() {
        const source = new Translatable_1.Translatable(this.payload.modifier.source).getTranslation();
        const attributes = this.transaction.sheet.getSheetAttributes().getValues();
        const calculator = new Modifier_1.FixedModifierAppliableValueCalculator(attributes);
        const value = this.payload.modifier.getAppliableValue(calculator);
        const valueWithSign = new ModifierValue_1.ModifierValue(value).getValueWithSign();
        return `${source}: ${valueWithSign} PM.`;
    }
}
exports.AddFixedModifierToManaPoints = AddFixedModifierToManaPoints;
