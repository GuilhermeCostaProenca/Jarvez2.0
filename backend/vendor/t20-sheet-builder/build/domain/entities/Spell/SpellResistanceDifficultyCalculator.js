"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SpellResistanceDifficultyCalculator = void 0;
class SpellResistanceDifficultyCalculator {
    static get baseResistanceDifficulty() {
        return 10;
    }
    static calculate(sheet, spellsAttribute) {
        const attributes = sheet.getSheetAttributes().getValues();
        const spellsAttributeValue = attributes[spellsAttribute];
        return 10 + Math.floor(sheet.getLevel() / 2) + spellsAttributeValue;
    }
}
exports.SpellResistanceDifficultyCalculator = SpellResistanceDifficultyCalculator;
