"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SheetDefense = void 0;
const Context_1 = require("../Context");
const Defense_1 = require("../Defense/Defense");
const DefenseTotalCalculatorFactory_1 = require("../Defense/DefenseTotalCalculatorFactory");
class SheetDefense {
    constructor(defense = new Defense_1.Defense()) {
        this.defense = defense;
    }
    addFixedModifier(modifier) {
        this.defense.addFixedModifier(modifier);
    }
    getTotal(attributes, armorBonus, shieldBonus) {
        const calculator = DefenseTotalCalculatorFactory_1.DefenseTotalCalculatorFactory.make(attributes, armorBonus, shieldBonus);
        return this.defense.getTotal(calculator);
    }
    getDefense() {
        return this.defense;
    }
    serialize(sheet, context = new Context_1.OutOfGameContext()) {
        const attributes = sheet.getSheetAttributes().getValues();
        const inventory = sheet.getSheetInventory();
        const armorBonus = inventory.getArmorBonus();
        const shieldBonus = inventory.getShieldBonus();
        const totalCalculator = DefenseTotalCalculatorFactory_1.DefenseTotalCalculatorFactory.make(attributes, armorBonus, shieldBonus);
        return {
            attribute: this.defense.attribute,
            fixedModifiers: this.defense.fixedModifiers.serialize(sheet, context),
            total: this.defense.getTotal(totalCalculator),
        };
    }
}
exports.SheetDefense = SheetDefense;
