"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const FixedModifier_1 = require("../Modifier/FixedModifier/FixedModifier");
const GeneralPowerName_1 = require("../Power/GeneralPower/GeneralPowerName");
const Defense_1 = require("./Defense");
const DefenseTotalCalculatorFactory_1 = require("./DefenseTotalCalculatorFactory");
describe('Defense', () => {
    it('should calc defense total', () => {
        const defense = new Defense_1.Defense();
        const attributes = { charisma: 0, constitution: 0, dexterity: 0, intelligence: 0, strength: 0, wisdom: 0 };
        const calculator = DefenseTotalCalculatorFactory_1.DefenseTotalCalculatorFactory.make(attributes, 0, 0);
        expect(defense.getTotal(calculator)).toBe(10);
    });
    it('should calc defense total with modifiers', () => {
        const defense = new Defense_1.Defense();
        defense.fixedModifiers.add(new FixedModifier_1.FixedModifier(GeneralPowerName_1.GeneralPowerName.dodge, 2));
        const attributes = { charisma: 0, constitution: 0, dexterity: 2, intelligence: 0, strength: 0, wisdom: 0 };
        const calculator = DefenseTotalCalculatorFactory_1.DefenseTotalCalculatorFactory.make(attributes, 0, 0);
        expect(defense.getTotal(calculator)).toBe(14);
    });
});
