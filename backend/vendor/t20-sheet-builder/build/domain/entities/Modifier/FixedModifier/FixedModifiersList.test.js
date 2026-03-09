"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const RaceAbilityName_1 = require("../../Race/RaceAbilityName");
const RoleName_1 = require("../../Role/RoleName");
const FixedModifier_1 = require("./FixedModifier");
const FixedModifiersList_1 = require("./FixedModifiersList");
const FixedModifiersListTotalCalculator_1 = require("./FixedModifiersListTotalCalculator");
describe('FixedModifiersList', () => {
    it('should calculate total', () => {
        const list = new FixedModifiersList_1.FixedModifiersList();
        list.add(new FixedModifier_1.FixedModifier(RaceAbilityName_1.RaceAbilityName.hardAsRock, 3));
        list.add(new FixedModifier_1.FixedModifier(RoleName_1.RoleName.arcanist, 8, new Set(['constitution'])));
        const calculator = new FixedModifiersListTotalCalculator_1.FixedModifiersListTotalCalculator({ charisma: 0, constitution: 2, dexterity: 0, intelligence: 0, strength: 0, wisdom: 0 });
        expect(list.getTotal(calculator)).toBe(13);
    });
});
