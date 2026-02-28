"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ModifierAppliableValueCalculator = void 0;
class ModifierAppliableValueCalculator {
    constructor(attributes) {
        this.attributes = attributes;
    }
    getAttributesBonusesTotal(attributeBonuses) {
        return attributeBonuses.reduce((acc, attribute) => this.attributes[attribute] + acc, 0);
    }
}
exports.ModifierAppliableValueCalculator = ModifierAppliableValueCalculator;
