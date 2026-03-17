"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const Level_1 = require("../../Sheet/Level");
const RoleAbilityName_1 = require("../../Role/RoleAbilityName");
const RoleName_1 = require("../../Role/RoleName");
const PerLevelModifier_1 = require("./PerLevelModifier");
const PerLevelModifiersList_1 = require("./PerLevelModifiersList");
const PerLevelModifiersListTotalCalculator_1 = require("./PerLevelModifiersListTotalCalculator");
describe('PerLevelModifiersList', () => {
    it('should calculate total', () => {
        const list = new PerLevelModifiersList_1.PerLevelModifiersList();
        list.add(new PerLevelModifier_1.PerLevelModifier({
            source: RoleName_1.RoleName.arcanist,
            value: 6,
            includeFirstLevel: true,
            attributeBonuses: new Set(['intelligence']),
        }));
        list.add(new PerLevelModifier_1.PerLevelModifier({
            source: RoleAbilityName_1.RoleAbilityName.arcanistSpells,
            value: 1,
            includeFirstLevel: false,
        }));
        const calculator = new PerLevelModifiersListTotalCalculator_1.PerLevelModifiersListTotalCalculator({ charisma: 0, constitution: 0, dexterity: 0, intelligence: 2, strength: 0, wisdom: 0 }, Level_1.Level.three);
        expect(list.getTotal(calculator)).toBe(26);
    });
    it('should calculate total with custom frequency', () => {
        const list = new PerLevelModifiersList_1.PerLevelModifiersList();
        list.add(new PerLevelModifier_1.PerLevelModifier({
            source: RoleName_1.RoleName.arcanist,
            value: 6,
            includeFirstLevel: true,
            attributeBonuses: new Set(['intelligence']),
        }));
        list.add(new PerLevelModifier_1.PerLevelModifier({
            source: RoleAbilityName_1.RoleAbilityName.arcanistSpells,
            value: 1,
            includeFirstLevel: false,
        }));
        list.add(new PerLevelModifier_1.PerLevelModifier({
            source: RoleAbilityName_1.RoleAbilityName.arcanistPath,
            value: 5,
            includeFirstLevel: false,
            frequency: 2,
        }));
        const calculator = new PerLevelModifiersListTotalCalculator_1.PerLevelModifiersListTotalCalculator({ charisma: 0, constitution: 0, dexterity: 0, intelligence: 2, strength: 0, wisdom: 0 }, Level_1.Level.three);
        expect(list.getTotal(calculator)).toBe(31);
    });
    it('should calculate total per level after first level', () => {
        const list = new PerLevelModifiersList_1.PerLevelModifiersList();
        list.add(new PerLevelModifier_1.PerLevelModifier({
            source: RoleName_1.RoleName.arcanist,
            value: 6,
            includeFirstLevel: true,
            attributeBonuses: new Set(['intelligence']),
        }));
        list.add(new PerLevelModifier_1.PerLevelModifier({
            source: RoleAbilityName_1.RoleAbilityName.arcanistSpells,
            value: 1,
            includeFirstLevel: false,
        }));
        expect(list.getTotalPerLevel(Level_1.Level.two)).toBe(7);
    });
    it('should calculate total per level on first level', () => {
        const list = new PerLevelModifiersList_1.PerLevelModifiersList();
        list.add(new PerLevelModifier_1.PerLevelModifier({
            source: RoleName_1.RoleName.arcanist,
            value: 6,
            includeFirstLevel: true,
            attributeBonuses: new Set(['intelligence']),
        }));
        list.add(new PerLevelModifier_1.PerLevelModifier({
            source: RoleAbilityName_1.RoleAbilityName.arcanistSpells,
            value: 1,
            includeFirstLevel: false,
        }));
        expect(list.getTotalPerLevel(Level_1.Level.one)).toBe(6);
    });
});
