"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AddPerLevelModifierToManaPoints = void 0;
const ModifierValue_1 = require("../Modifier/ModifierValue");
const Translatable_1 = require("../Translatable");
const Action_1 = require("./Action");
class AddPerLevelModifierToManaPoints extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'addPerLevelModifierToManaPoints' }));
    }
    execute() {
        const manaPoints = this.transaction.sheet.getSheetManaPoints();
        manaPoints.addPerLevelModifier(this.payload.modifier);
    }
    getDescription() {
        const source = new Translatable_1.Translatable(this.payload.modifier.source).getTranslation();
        const value = new ModifierValue_1.ModifierValue(this.payload.modifier.baseValue).getValueWithSign();
        const includeFirstLevel = this.payload.modifier.includeFirstLevel ? '' : ' após o nivel 1';
        return `${source}: ${value} PM por nível${includeFirstLevel}.`;
    }
}
exports.AddPerLevelModifierToManaPoints = AddPerLevelModifierToManaPoints;
