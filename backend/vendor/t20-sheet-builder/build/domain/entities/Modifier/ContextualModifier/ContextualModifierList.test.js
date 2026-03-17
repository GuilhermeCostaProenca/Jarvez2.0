"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const InGameContextFake_1 = require("../../Context/InGameContextFake");
const RaceAbilityName_1 = require("../../Race/RaceAbilityName");
const ContextualModifier_1 = require("./ContextualModifier");
const ContextualModifierList_1 = require("./ContextualModifierList");
const ContextualModifiersListTotalCalculator_1 = require("./ContextualModifiersListTotalCalculator");
const isUnderground = (context) => { var _a, _b; return (_b = (_a = context.getCurrentLocation()) === null || _a === void 0 ? void 0 : _a.isUnderground) !== null && _b !== void 0 ? _b : false; };
describe('ContextualModifierList', () => {
    it('should calculate total', () => {
        const list = new ContextualModifierList_1.ContextualModifiersList();
        list.add(new ContextualModifier_1.ContextualModifier({
            source: RaceAbilityName_1.RaceAbilityName.rockKnowledge,
            value: 2,
            condition: { description: 'any', verify: isUnderground },
        }));
        list.add(new ContextualModifier_1.ContextualModifier({
            source: RaceAbilityName_1.RaceAbilityName.rockKnowledge,
            value: 2,
            condition: { description: 'any', verify: isUnderground },
            attributeBonuses: new Set(['constitution']),
        }));
        list.add(new ContextualModifier_1.ContextualModifier({
            source: RaceAbilityName_1.RaceAbilityName.hardAsRock,
            value: 2,
            condition: { description: 'any', verify: context => !isUnderground(context) },
        }));
        const totalCalculator = new ContextualModifiersListTotalCalculator_1.ContextualModifiersListTotalCalculator(new InGameContextFake_1.InGameContextFake(), { charisma: 0, constitution: 2, dexterity: 0, intelligence: 0, strength: 0, wisdom: 0 });
        const total = list.getTotal(totalCalculator);
        expect(total).toBe(6);
    });
    it('should calculate max total', () => {
        const list = new ContextualModifierList_1.ContextualModifiersList();
        list.add(new ContextualModifier_1.ContextualModifier({
            source: RaceAbilityName_1.RaceAbilityName.rockKnowledge,
            value: 2,
            condition: { description: 'any', verify: isUnderground },
        }));
        list.add(new ContextualModifier_1.ContextualModifier({
            source: RaceAbilityName_1.RaceAbilityName.rockKnowledge,
            value: 2,
            condition: { description: 'any', verify: isUnderground },
            attributeBonuses: new Set(['constitution']),
        }));
        list.add(new ContextualModifier_1.ContextualModifier({
            source: RaceAbilityName_1.RaceAbilityName.hardAsRock,
            value: 2,
            condition: { description: 'any', verify: context => !isUnderground(context) },
        }));
        const attributes = {
            charisma: 0,
            constitution: 2,
            dexterity: 0,
            intelligence: 0,
            strength: 0,
            wisdom: 0,
        };
        expect(list.getMaxTotal(attributes)).toBe(8);
    });
});
